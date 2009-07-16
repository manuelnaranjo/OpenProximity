#!/usr/bin/env python
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

import gobject

import dbus
import dbus.service
import dbus.glib
import dbus.mainloop.glib

from re import compile

url="net.aircable.RemoteScanner"

class ConnectionFailed(dbus.DBusException):
    _dbus_error_name="%s.ConnectionFailed" % url
    
def AddDots(address):
    address = address.strip()
    out = ""
    for i in range(0,5):
	out+=address[i*2:(i+1)*2]+":"
    out+=address[10:12]
    return out
    
class RemoteScanner(dbus.service.Object):
    local = None
    remote = None
    #found = dict()
    
    record_pattern = compile("[0-9A-F]{12} RSSI.*")
    
    def __scan(self):
	print "__scan"
	
	try:
    	    client = sppClient(
		target = self.remote,
		channel = 1,
		service = "spp",
		device = self.local
	    )
	    
	    client.connect()
    	    self.ScannerConnected(self.local, self.remote)
	    self.PropertyChanged('Discovering', 1)
	    
	    client.socket.settimeout(30)
	    print client.readLine()
	    print client.readBuffer()
	    client.sendLine("r1")
	    print client.readBuffer()

	    flag = True
	    while ( flag ):
		lines=client.readBuffer(honnor_eol=True,timeout=1)

		for line in lines.splitlines():
		    if self.record_pattern.match(line.strip()):
			address, rssi = line.split('RSSI')
			self.DeviceFound( AddDots(address) , {'RSSI': int(rssi)})
		    elif line.find('COMMAND') >-1:
			print "RSSI completed"
			flag = False
			break

	    client.sendLine('c')
    	    client.disconnect()
	except Exception, err:
	    try:
		client.sendLine('c')
		client.disconnect()
	    except:
		pass
	    self.ScannerDisconnected(self.local, self.remote)
	    self.PropertyChanged('Discovering', 0)
	    self.ConnectionException(str(err))
	    return False
	
	self.ScannerDisconnected(self.local, self.remote)
	self.PropertyChanged('Discovering', 0)
	return False
    
    @dbus.service.signal(url, signature="s")
    def ConnectionException(self, text):
	print "ConnectionException", text
    
    @dbus.service.signal(url, signature="sa{si}")
    def DeviceFound(self, address, values):
	# simulate bluez format
	print "Found %s: %s" % (address, values )
	
    @dbus.service.signal(url, signature="ss")
    def ScannerConnected(self, local, remote):
	print "ScannerConnected %s: %s" % (local, remote )

    @dbus.service.signal(url, signature="ss")
    def ScannerDisconnected(self, local, remote):
	print "ScannerDisconnected %s: %s" % (local, remote )
	
    @dbus.service.signal(url, signature="si")
    def PropertyChanged(self, name, value):
	print "PropertyChanged %s: %s" % (name, value)
    
    @dbus.service.method( url, in_signature="ss", out_signature="")
    def StartScan(self, local, remote):
	print "StartScan", str(local), str(remote)
	self.local = local
	self.remote = remote
	gobject.timeout_add(1000, self.__scan)
	return
	
if __name__=='__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    gobject.threads_init()
    dbus.glib.init_threads()
    
    bus = dbus.SystemBus()
    name = dbus.service.BusName(url, bus)
    object = RemoteScanner(bus, '/RemoteScanner' )
    
    from net.aircable.spp import sppClient
    mainloop = gobject.MainLoop()
    print "Running RemoteScanner Service."
    mainloop.run()
