#!/usr/bin/env python
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Test client for RemoteScanner service
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


import sys
from traceback import print_exc

import gobject
import dbus, dbus.mainloop.glib

from math import sqrt, pow

url = "net.aircable.RemoteScanner"

rssi = list()

def average(inp):
    acu = 0.0
    for i in inp:
        acu+=i
    return acu / len(inp)
		    
def deviation(inp, av=None):
    if av is None:
        av = average(inp)
    acu = 0.0
    for i in inp:
        acu += pow(i-av,2)
    return sqrt( acu/len(inp) )
    
def connected(local, remote):
    print "ScannerConnected", local, remote

def disconnected(local, remote):
    print "ScannerDisconnected", local, remote
    global rssi
    av = average(rssi)
    dev=deviation(rssi, av)
    print av, dev    
    loop.quit()

def found(address, value):
    global rssi
    print "Device found:", address, int(value['RSSI'])
    rssi+=(float(value['RSSI']),)
    
def property(option, value):
    print "Property:", option, value
    
def exception(msg):
    print "Exception", msg
    loop.quit()

def main():
    bus = dbus.SystemBus()

    try:
	bus.add_signal_receiver(found, dbus_interface=url, signal_name="DeviceFound")
	bus.add_signal_receiver(connected, dbus_interface=url, signal_name="ScannerConnected")
	bus.add_signal_receiver(disconnected, dbus_interface=url, signal_name="ScannerDisconnected")
	bus.add_signal_receiver(exception, dbus_interface=url, signal_name="ConnectionException")
	bus.add_signal_receiver(property, dbus_interface=url, signal_name="PropertyChanged")
	
	print "Signals registered"
	
        remote_object = bus.get_object(url,
                                       "/RemoteScanner")
	iface = dbus.Interface(remote_object, url)

	iface.StartScan("00:50:C2:7F:EF:FE", "00:50:C2:7F:41:5B")
	print "scan started"
    except dbus.DBusException:
        print_exc()
        sys.exit(1)
    return False

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    gobject.timeout_add(15, main)
    loop = gobject.MainLoop()

    loop.run()
