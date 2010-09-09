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
from django.conf import settings

try:
    from net.aircable.utils import logger
except:
    import logging
    logger = logging.getLogger('sensorsdk')
    logger.setLevel(logging.DEBUG)
    c = logging.StreamHandler()
    c.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(c)

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

def save_email_settings(mail, *args, **kwargs):
    def store(mail):
	out = ""
	out+="#AUTO GENERATED EMAIL CONFIG\n"
	for key, val in mail.iteritems():
	    out+='%s="%s"\n' % ( key, val)
	    setattr(settings, key, val)
	out+="#END AUTO GENERATED EMAIL CONFIG\n"
	return out

    print "save email", mail
    inp = file(settings.OPENPROXIMITY_CONFIG_FILE, "r")
    lines = inp.readlines()
    inp.close()
    
    out = ""
    #file(conf.OPENPROXIMITY_CONFIG_FILE, "w")
    flag = False
    conf_stored = False
    for line in lines:
	if line.startswith("#AUTO GENERATED EMAIL CONFIG"):
	    flag = True
	elif line.startswith("#END AUTO GENERATED EMAIL CONFIG"):
	    out+=store(mail)
	    flag = False
	    conf_stored = True
	elif not flag:
	    out+=line.strip()
	    out+="\n"
    if not conf_stored:
	out+=store(mail)
    f = file(settings.OPENPROXIMITY_CONFIG_FILE, "w")
    f.write(out)
    f.close()
    print out
