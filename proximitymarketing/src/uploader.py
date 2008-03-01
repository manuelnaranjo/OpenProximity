import dbus
import gobject
import dbus.glib
from net.aircable import Scan
from net.aircable import SDP
from net.aircable import Upload
from threading import Thread

profile = 'opp'
file_to_send = '/home/manuel/proximitymarketing/proximitymarketing/src/image.jpg'

class WorkerThread (Thread):
    def __init__ ( self, addr , adapter, file_to_send , profile):
	self.addr = addr
	self.adapter = adapter
	self.file_to_send = file_to_send
	self.profile = profile
	Thread.__init__ (self)
    
    def connected_test(self, uploader):
	uploader.sendFile(self.file_to_send)
	#We could send more than one file with one connection?

    def transfer_completed_test(self, uploader):
	uploader.disconnectBT()
    
    def closed_test(self, uploader):
	print 'All Done'

    
    def cancelled(self, uploader):
	print 'Someone Cancelled the Upload'
	uploader.disconnectBT()

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
	self.uploader.connected = self.connected_test
        self.uploader.completed = self.transfer_completed_test
	self.uploader.closed = self.closed_test
	self.uploader.cancelled = self.cancelled
    
	self.uploader.connectBT(self.addr, 
	    '%s:%i'%(self.profile, self.channel) )
    
def test_firsttime(addr):
    WorkerThread( addr, adapter, file_to_send, profile ).start()
    
if __name__ == "__main__":
    bus = dbus.SystemBus();


    obj = bus.get_object('org.bluez', '/org/bluez/hci0')
    adapter = dbus.Interface(obj, 'org.bluez.Adapter')

    sc = Scan(adapter)
    sc.firsttimefound = test_firsttime
    sc.register_signals()
    sc.start_scanning()

    gobject.threads_init()
    dbus.glib.init_threads()
    main_loop = gobject.MainLoop()
    main_loop.run()
