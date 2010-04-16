# -*- coding: utf-8 -*-
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Plugin system base
import os, re, StringIO, zipfile
import ConfigParser, pkgutil, traceback
import sys,functools
from net.aircable.utils import logger


try:
    import plugins
except Exception, err:
    import new
    logger.error("no plugins dir found")
    plugins = new.module('plugins')
    plugins.__path__=[]

def find_plugin_dirs():
        return [os.path.expanduser('~/.openproximity/plugins'),
                '/usr/lib/openproximity/plugins']

# add dirs from sys.path:
plugins.__path__ = pkgutil.extend_path(plugins.__path__, 
                                              plugins.__name__)
# add dirs specific to sensorsdk:
plugins.__path__ = find_plugin_dirs() + plugins.__path__

class Plugin(object):
	def __loadFromFile(self, path):
		p = os.path.join(path, 'plugin.py')
	        if not os.path.isfile(p):
	    	    raise Exception("plugin not suported %s" % path)
	        A=file(p, 'r')
                content = A.read()
                A.close()
                content=compile(content, p, 'exec')
                glob = dict()
                loc = dict()
                eval(content, glob, loc)
                self.provides = loc
                if "post_environ" in self.provides:
                   self.post_environ=self.provides['post_environ']


        def __init__(self, path=None, name=None, egg=None):#, load, egg):
    		if not egg:
            	    self.path = os.path.join(path, name)
            	else:
            	    self.path = path
            	if not egg:
            	    self.name = 'plugins.%s' % name
            	else:
            	    self.name = name
                self.egg = egg
                if not self.egg:
                      self.__loadFromFile(self.path)
                else:
                     raise Exception("plugin not suported %s" % path)
                self.enabled = self.provides.get('enabled', False)
                self.__module = None
                self.__version = None
                self.__version_info = None
                self.__rpc = None
                logger.info("Plugin: %s registered" % self.name)

	@property
	def module(self):
	    if self.__module is None:
		self.__import_plugin()
	    return self.__module

	@property
	def __version__(self):
	    if self.__version is None:
		self.__version=getattr(self.module, '__version__', 'ND')
	    return self.__version

	@property
	def __version_info__(self):
	    if self.__version_info is None:
		self.__version_info=getattr(self.module, '__version_info__', 'ND')
	    return self.__version_info

	@property
	def rpc(self):
	    if self.__rpc is None:
		rpc = __import__("%s.rpc" % self.name, {}, {}, ['handle', 'register'])
		self.__rpc = {}
		self.__rpc['handle'] = getattr(rpc, 'handle', None)
		self.__rpc['register'] = getattr(rpc, 'register', None)
		self.__rpc['found_action'] = getattr(rpc, 'found_action', None)
	    return self.__rpc

        def __import_plugin(self):
            plugin=__import__(self.name, {}, {}, [], 0)
            try:
                plugin=getattr(plugins, self.name.split('.',1)[-1])
            except Exception, err:
            	logger.error('plugin was not part of plugins.*')
    		logger.exception(err)
            self.__module=plugin


class PluginSystem(object):
        def __init__(self):
                self.plugin_infos = None

        def get_plugins(self, provides=None):
                for i in self.plugin_infos.itervalues():
                     if not provides or i.provides.get(provides, None):
                          yield i

        def _find_plugins_for_egg(self, egg_name):
	    b=zipfile.PyZipFile(egg_name)
	    for a in b.namelist():
		if not a.startswith('EGG-INFO') and a.endswith('__init__.py'):
		    try:
			if not egg_name in sys.path:
			    sys.path.append(egg_name)
                        self.load_info(egg_name, a.split('/')[0], egg=True)
                        return
                    except Exception, err:
			logger.error("Failed to load info from egg file: %s" % egg_name)
			logger.exception(err)
	    logger.info("no plugin in egg %s" % egg_name)

        def find_plugins(self):
    		if self.plugin_infos is not None:
    		    return
    		logger.info("looking for plugins")
    		self.plugin_infos=dict()
                for path in plugins.__path__:
                        if not os.path.isdir(path):
                                continue
                        for entry in os.listdir(path):
                                if entry.startswith('_'):
                                        continue # __init__.py etc.
                                if entry.endswith('.py') or os.path.isdir( os.path.join(path, entry) ):
                                        try:
                                                self.load_info(path, entry.split('.')[0])
                                        except Exception, err:
                                                logger.error("Failed to load info %s" % entry)
				if entry.endswith('.egg'):
				    self._find_plugins_for_egg(os.path.join(path, entry))

        def load_info(self, path, name, egg=False):
		if not egg:
		    _name='plugins.%s' % name
		else:
		    _name=name
		logger.info("Plugin: load_info %s" % name)
                plugin = Plugin(path, name, egg)
		if plugin.enabled:
		    self.plugin_infos[name]=plugin
		logger.info("Plugin: %s ready" % _name)


	def post_environ(self):
	    from django.db.models.loading import load_app
	    for plugin in self.get_plugins():
		if plugin.provides.get('post_environ', False):
		    plugin.module.post_environ()
	    for plugin in self.get_plugins():
		load_app(plugin.name)

pluginsystem = PluginSystem()

if __name__=='__main__':
    pluginsystem.find_plugins()
    for plug in pluginsystem.get_plugins():
        print plug.provides
