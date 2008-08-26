#!/usr/bin/python
#    OpenProximity: Main app.
#    Copyright (C) 2008 Manuel Naranjo <manuel@aircable.net>
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
#

import dbus
import gobject
import dbus.glib
import os
from net.aircable.openproximity import Scan
from net.aircable.openproximity import SDP
from net.aircable.openproximity import Upload
from threading import Thread


if 'OP_PROFILE' in os.environ.keys():
    profile = os.environ['OP_PROFILE']
else:
    profile = 'opp'

if 'OP_FILE' in os.environ.keys():
    file_to_send = os.environ['OP_FILE']
else:
    file_to_send = '%s/%s' %(os.environ['HOME'], 'openproximity/image.jpg')
    
name = 'OpenProximity v0.1.2'

def connected_test(uploader):
    uploader.sendFile(file_to_send)
    #We could send more than one file with one connection?

def transfer_completed_test(uploader):
    uploader.disconnectBT()
    
def closed_test(uploader):
    print 'All Done'

    
def cancelled(uploader):
    print 'Someone Cancelled the Upload'
    uploader.disconnectBT()


class WorkerThread (Thread):
    def __init__ ( self, addr , adapter, profile):
	self.addr = addr
	self.adapter = adapter
	self.profile = profile
	Thread.__init__ (self)
        
    def run( self ):
    	self.setName('OpenProximity, servicing: %s' % self.addr )
    	print "Running thread for: %s" %self.addr
    	self.sdp = SDP(self.adapter)
    	self.handle = self.sdp.hasService( self.addr, profile ) 
    	if self.handle <= 0:
            print "Device doesn't have profile %s" %self.profile
            print "Thread ending: %s" %self.addr
            return 
        
    	self.channel = self.sdp.getHandleChannel( self.addr, self.handle)
    	print "Using channel: %i" %self.channel
        
    	self.uploader = Upload(bus)
    	self.uploader.connected = connected_test
        self.uploader.transfer_completed = transfer_completed_test
    	self.uploader.closed = closed_test
    	self.uploader.cancelled = cancelled
        
    	self.uploader.connectBT(self.addr, 
    	    '%s:%i'%(self.profile, self.channel) )
    
def test_firsttime(addr):
    WorkerThread( addr, adapter, profile ).start()
    
if __name__ == "__main__":
    bus = dbus.SystemBus();


    obj = bus.get_object('org.bluez', '/org/bluez/hci0')
    adapter = dbus.Interface(obj, 'org.bluez.Adapter')
    adapter.SetName(name)
    
    sc = Scan(adapter)
    sc.firsttimefound = test_firsttime
    sc.register_signals()
    sc.start_scanning()

    gobject.threads_init()
    dbus.glib.init_threads()
    main_loop = gobject.MainLoop()
    main_loop.run()

