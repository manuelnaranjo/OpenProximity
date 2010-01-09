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
	logger=logging.getLogger('openproximity')
	logger.setLevel(logging.DEBUG)
	
	formatter=logging.Formatter('%(asctime)-12s %(name)-4s: %(levelno)-2s %(message)s')
	
	if os.environ.get('CONSOLE_LOG') == 'yes' or \
		os.environ.get('DEBUG')=="yes":
	    console=logging.StreamHandler()
	    console.setLevel(logging.DEBUG)
	    console.setFormatter(formatter)
	    logger.addHandler(console)

	if os.environ.get('LOG_PORT') is not None:
	    socketHandler=logging.handlers.SocketHandler('localhost',
		os.environ.get('LOG_PORT'))
	    #socketHandler.addFormatter(formatter)
	    logger.addHandler(socketHandler)
	
	if os.environ.get('LOG_FILE', None) is not None:
	    log_=logging.handlers.RotatingFileHandler(
		os.environ.get('LOG_FILE'),
		maxBytes=1024*512, #512KB,
		backupCount=5 #2.5MB log
	    )
	    formatter=logging.Formatter('%(asctime)-12s %(levelname)-8s %(pathname)s/%(module)s:%(funcName)s[%(thread)d]\t%(message)s')
	    log_.setLevel(logging.DEBUG)
	    log_.setFormatter(formatter)
	    logger.addHandler(log_)
	return logger
	
def logmain(app):
    logger.info("%s start up, arguments %s" % (app, sys.argv))

# some shared variables
logger = __initLog()
