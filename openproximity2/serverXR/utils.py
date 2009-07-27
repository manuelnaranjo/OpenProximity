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

def getDefaultSettings():
    return {
	'MEDIA_ROOT': 	'/tmp/aircable',
	'TIMEOUT':	15
    }

#settings storing
def store_settings():
	keys = getDefaultSettings()
	
	try:
		path = os.path.dirname( os.path.realpath( settings.__file__ ))
	except:
		path = os.path.dirname( os.path.realpath( __file__ ))
	
	out = file( os.path.join(path, 'settings.py'), 'w' )
	
	out.write('''# Automatically saved configuration
# Saved on %s
#
# known keys and default values are:
''' % time.asctime())
	
	for key, default in keys.items():
		out.write('# %s: %s\n' % (key, default))    
	
	out.write('''# SCANNERS is a dict of address: priority, where priority is a number that tells
# how many times each dongle should do an inquiry cycle per SCANNER cycle
# UPLOADERS is a list of address that tells which dongles should be usign for inquiry''')
	out.write('\n')
	
	for key, default in keys.items():
		val=getattr(settings, key, default)
		if val is not None:
			if type(val)==str:
				out.write('%s = "%s"\n' % (key, val))
			else:
				out.write('%s = %s\n' % (key, val))
	out.close()

#init logging
def __initLog():
	logger=logging.getLogger('openproximity')
	logger.setLevel(logging.DEBUG)
	
	formatter=logging.Formatter('%(asctime)-12s %(name)-4s: %(levelno)-2s %(message)s')
	
	if os.environ.get('LOG_PORT') is not None:
	    socketHandler=logging.handlers.SocketHandler('localhost',
		os.environ.get('LOG_PORT'))
	    #socketHandler.addFormatter(formatter)
	    logger.addHandler(socketHandler)
	    logger.info('Socket Handler ready')
	
	if os.environ.get('CONSOLE_LOG') == 'yes':
	    console=logging.StreamHandler()
    	    console.setLevel(logging.DEBUG)
	    console.setFormatter(formatter)
	    logger.addHandler(console)
	    logger.info('Console Handler Ready')
	
	if os.environ.get('LOG_FILE', None) is not None:
	    log_=logging.FileHandler(os.environ.get('LOG_FILE'))
    	    log_.setLevel(logging.DEBUG)
	    log_.setFormatter(formatter)
	    logger.addHandler(log_)
	    logger.info('File Handler Ready')
	    
	return logger

# some shared variables
logger = __initLog()

try:
	import settings
	logger.debug('Found settings')
except:
	logger.debug('No settings, using default')
	import new
	settings=new.module('openproximity.settings')
	for key, default in getDefaultSettings().items():
	    setattr(settings, key, default)
	import os
	os.system('mkdir -p %s' % settings.MEDIA_ROOT)
