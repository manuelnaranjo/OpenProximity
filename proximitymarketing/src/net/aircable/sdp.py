#    Proximity Marketing Solution: This file will resolve sdp records for
#                a certain device.
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
import xml.dom.minidom

class SDP:
    
    adapter = None
    
    def __init__(self, adapter):
        self.adapter = adapter
    
    def getHandleChannel(self, bt_addr, handle):
        XML=self.adapter.GetRemoteServiceRecordAsXML(bt_addr, handle)
            
        doc=xml.dom.minidom.parseString( XML )
    
        nodes = doc.getElementsByTagName('attribute')
        for node in nodes:
            if node.getAttribute('id') == '0x0004':
                nodes_ = node.getElementsByTagName('uuid')
                for node_ in nodes_:
                    if node_.getAttribute('value') == '0x0003':
                        while node_.nextSibling.nodeType!=node.ELEMENT_NODE:
                            node_ = node_.nextSibling
                        value = int(node_.nextSibling.getAttribute('value'), 16) 
                        return value
        return None
                              
    
    def hasService(self, bt_addr, profile):
        handle = self.adapter.GetRemoteServiceHandles(bt_addr, profile)
        if len(handle) > 0:
            return handle[0] #stupid way to do it, but works by now.
        
        return 0

if __name__ == "__main__":
    bus = dbus.SystemBus();
    
    services = [
        'vcp',
        'pbap',
        'sap',
        'ftp',
        'bpp',
        'bip',
        'synch',
        'dun',
        'opp',
        'fax',
        'spp',
        'hsp'
        #'panu',
        #'nap'
        ]

    #DON'T FORGET TO DEFINE THIS FOR TESTING!!!!!    
    bt_addr=''
    
    obj = bus.get_object('org.bluez', '/org/bluez/hci0')
    adapter = dbus.Interface(obj, 'org.bluez.Adapter')

    for service in services:
        handle = hasService(bt_addr, adapter, service)
    
        if handle != 0:
            print 'sevice: %s\thandle %i\tchannel: %i' % ( service, 
                                handle , getHandleChannel(bt_addr, adapter, handle) )

