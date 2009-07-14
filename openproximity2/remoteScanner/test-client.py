#!/usr/bin/env python

import sys
from traceback import print_exc

import gobject
import dbus, dbus.mainloop.glib

url = "net.aircable.RemoteScanner"

def connected(local, remote):
    print "ScannerConnected", local, remote

def disconnected(local, remote):
    print "ScannerDisconnected", local, remote
    loop.quit()

def found(address, value):
    print "Device found:", address, int(value['RSSI'])
    
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
