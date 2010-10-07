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
import const
import logging
import logging.handlers
import os, sys, time

def isAIRcable(address):
	return address[:8].upper() in const.AIRCABLE_MAC

#init logging
def __initLog():
	logger=logging.getLogger()
	logger.setLevel(logging.NOTSET)
	
	logger=logging.getLogger('openproximity')
	logger.setLevel(logging.DEBUG)
	formatter=logging.Formatter('%(asctime)-12s %(pathname)s/%(module)s:%(funcName)s: %(levelno)-2s %(message)s')
	
	if os.environ.get('LOG_FILE', None) is not None:
	    log_=logging.handlers.RotatingFileHandler(
		os.environ.get('LOG_FILE'),
		maxBytes=1024*512, #512KB,
		backupCount=5 #2.5MB log
	    )
	    format=logging.Formatter('%(asctime)-12s %(levelname)-8s %(pathname)s/%(module)s:%(funcName)s[%(thread)d]\t%(message)s')
	    log_.setLevel(logging.DEBUG)
	    log_.setFormatter(format)
	    logger.addHandler(log_)
	
	
	if os.environ.get('CONSOLE_LOG') == 'yes' or \
		os.environ.get('DEBUG')=="yes":
	    console=logging.StreamHandler()
	    console.setFormatter(formatter)
	    logger.addHandler(console)

	if os.environ.get('LOG_PORT') is not None:
	    socketHandler=logging.handlers.SocketHandler('localhost',
		os.environ.get('LOG_PORT'))
	    socketHandler.addFormatter(formatter)
	    logger.addHandler(socketHandler)
	
	
	return logger
	
def logmain(app):
    logger.info("%s start up, arguments %s" % (app, sys.argv))

# some shared variables
logger = __initLog()

def trace():
    try:
#	from pydbgr.api import debug as set_trace
	from pudb import set_trace
        import urwid
        def t(*args, **kwargs):
	    pass
	urwid.raw_display.Screen.signal_init=t
	urwid.raw_display.Screen.signal_restore=t
    except Exception, err:
	logger.warning("Using non multithreaded pdb")
    	from pdb import set_trace 
    return set_trace()

def register_debug_shell():
  ''' 
    a helper function that will allow to start pdb or pudb
    when CTRL-C is received
  '''
  if 'PDB' not in os.environ:
      return

  logger.debug("Registering PDB debugger")
  def signal_handler(signal, frame):
	trace()
  import signal
  signal.signal(signal.SIGINT, signal_handler)

register_debug_shell()

def get_subclass(object):
    for related in object._meta.get_all_related_objects():
	if type(object) in related.model._meta.get_parent_list():
	    if hasattr(object,related.var_name):
		return get_subclass(getattr(object, related.var_name))
    return object

def get_subclasses(klass):
    out = [klass, ]
    if len(klass.__subclasses__()) > 0:
	for k in klass.__subclasses__():
	    out.extend(get_subclasses(k))
    return out
