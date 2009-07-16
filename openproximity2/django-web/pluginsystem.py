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
import os, re, StringIO
import ConfigParser, pkgutil

import plugins

def find_plugin_dirs():
        return [os.path.expanduser('~/.openproximity/plugins'),
                '/usr/lib/openproximity/plugins']

# add dirs from sys.path:
plugins.__path__ = pkgutil.extend_path(plugins.__path__, 
                                              plugins.__name__)
# add dirs specific to sensorsdk:
plugins.__path__ = find_plugin_dirs() + plugins.__path__

class Plugin(object):
        def __init__(self, path, name, load):
                self.path = path
                self.name = name
    		_module = load()
		for i in dir(_module):
		    setattr(self, i, getattr(_module, i))
		self._module = _module
		self.provides = getattr(_module, 'provides')
		if 'django' not in self.provides or not self.provides['django']:
		    raise Exception("Not a django plugin, won't load here")

class PluginSystem(object):
        def __init__(self):
                self.plugin_infos = list()

        def get_plugins(self):
                return self.plugin_infos

        def find_plugins(self):
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
                                                print "Failed to load info:", 
                                                print os.path.join(path, entry)
						print err

        def load_info(self, path, name):
                plugin = Plugin(path, name,
                                lambda:self.import_plugin(name))

    		self.plugin_infos.append(plugin)

        def import_plugin(self, name):
                __import__('plugins.%s' % name, {}, {}, [], 0)
                plugin = getattr(plugins, name)
		
                return plugin

pluginsystem = PluginSystem()

if __name__=='__main__':
    pluginsystem.find_plugins()
    for plug in pluginsystem.get_plugins():
	print plug.provides
