#    Proximity Marketing Solution: This file is in charge of devices
#        scanning, and function calling after a new device has been found.
#    Copyright (C) 2008 Manuel Naranjo <manuel@aircable.net>
#    Copyright (C) 2000-2007 BlueZ Project, original file:
#                http://wiki.bluez.org/wiki/HOWTO/DiscoveringDevices
#
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import dbus
import dbus.glib
import gobject
import sdp

__DEBUG="yes"

def  debug ( *text ):
    if __DEBUG == None:
        return 
    print text
    
class Scan:
    __db={}
        
    def __init__(self, adapter):
        self.__adapter=adapter
        
    def __disc_started_signal(self):
        debug( 'Signal: DiscoveryStarted()' )
    
    def __rem_dev_found_signal(self, address, cls, rssi):
        if address not in self.__db:
            self.__db[address]='1'
            debug( 'First Time Found(%s, %s, %s)' % (address, cls, rssi) )
            if self.firsttimefound != None:
                self.firsttimefound(address)
        else:
            debug( 'Found Again(%s, %s, %s)' % (address, cls, rssi) )
    
    def __rem_dev_name_signal(self, address, name):
        debug( 'Signal: RemoteNameUpdated(%s, %s)' % (address, name) )
    
    def __disc_completed_signal(self):
        debug( 'Signal: DiscoveryCompleted()' )
        #main_loop.quit()
    
    def register_signals(self):
        self.__adapter.connect_to_signal('DiscoveryStarted', 
                                       self.__disc_started_signal )
        self.__adapter.connect_to_signal('RemoteDeviceFound',
                                       self.__rem_dev_found_signal )
        self.__adapter.connect_to_signal('RemoteNameUpdated',
                                       self.__rem_dev_name_signal )
        self.__adapter.connect_to_signal('DiscoveryCompleted',
                                        self.__disc_completed_signal )
    
    def start_scanning(self):
        try:
            self.__adapter.StopPeriodicDiscovery()
        except dbus.DBusException, e:
            print "Ignoring: %s" %e
            
        self.__adapter.StartPeriodicDiscovery()
        self.__adapter.SetPeriodicDiscoveryNameResolving(0)

def test_firsttime(addr):
    print "Found %s for first time" %addr

#testing class
if __name__ == "__main__":
    bus = dbus.SystemBus();


    obj = bus.get_object('org.bluez', '/org/bluez/hci0')
    adapter = dbus.Interface(obj, 'org.bluez.Adapter')

    scanner = Scan(adapter)
    scanner.firsttimefound = test_firsttime
    scanner.register_signals()
    scanner.start_scanning()

    gobject.threads_init()
    dbus.glib.init_threads()
    main_loop = gobject.MainLoop()
    main_loop.run()
