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
#!/usr/bin/python

import sys
import dbus
import re

from utils import getLogger
logger=getLogger(__name__)

from lxml import etree

CHANNEL_XPATH=etree.XPath("/record/attribute[@id='0x0004']/sequence/sequence/uuid[@value='0x0003']/../uint8/@value")

OBEX_UUID='00001105-0000-1000-8000-00805f9b34fb'
FTP_UUID='00001106-0000-1000-8000-00805f9b34fb'

							
def resolve(address, uuid, adapter=None, bus=dbus.SystemBus()):
	try:
	    adapter.CreateDevice(address)
	    logger.debug("Device created: %s" % address)
	except:
	    logger.debug("Device all ready known: %s" % address)
	    
	path = adapter.FindDevice(address)
	
	device = dbus.Interface(bus.get_object("org.bluez", path),
							"org.bluez.Device")
	properties = device.GetProperties()
	
	if uuid in properties['UUIDs']:
	    services = device.DiscoverServices(uuid);
		
	    for key in services.keys():
		root=etree.XML(str(services[key]))
		res=CHANNEL_XPATH(root)
		if len(res)>0:
		    return int(res[0], 16)
	
	# lets check if the service is there now
	#adapter.RemoveDevice(path)
	
	raise Exception("UUID not found")
		
if __name__ == '__main__':
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.bluez.Manager")

    adapter = dbus.Interface(bus.get_object("org.bluez", manager.DefaultAdapter()),
							"org.bluez.Adapter")

    print resolve('00:15:E9:F5:BA:FE', OBEX_UUID, adapter, bus)
    print resolve('00:15:E9:F5:BA:FE', FTP_UUID, adapter, bus)
