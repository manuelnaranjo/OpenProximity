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
	
	socketHandler=logging.handlers.SocketHandler('localhost',
		logging.handlers.DEFAULT_TCP_LOGGING_PORT)
	#socketHandler.addFormatter(formatter)
	logger.addHandler(socketHandler)
	
	console=logging.StreamHandler()
	console.setLevel(logging.DEBUG)
	logger.addHandler(console)
	console.setFormatter(formatter)
	
	logger.info('Socket Handler ready')
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
