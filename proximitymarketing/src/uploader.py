import dbus
import gobject
import dbus.glib
from net.aircable import Scan
from net.aircable import SDP
from net.aircable import Upload

profile = 'opp'
file_to_send = 'AIRcable.vnt'

def connected_test(uploader):
    uploader.sendFile(file_to_send)

def transfer_completed_test(uploader):
    uploader.disconnectBT()
    
def closed_test(uploader):
    print 'All Done'
    exit(0)
    
def cancelled(uploader):
    print 'Someone Cancelled the Upload'
    uploader.disconnectBT()

def test_firsttime(addr):
    print "Found callback: %s" %addr
    sdp = SDP(adapter)
    handle = sdp.hasService( addr, profile ) 
    if handle <= 0:
        print "Device doesn't have profile %s" %profile
        return 
    
    channel = sdp.getHandleChannel( addr, handle)
    print "Using channel: %i" %channel
    
    uploader = Upload(bus)
    uploader.connected = connected_test
    uploader.completed = transfer_completed_test
    uploader.closed = closed_test
    uploader.cancelled = cancelled
    
    uploader.connectBT(addr, '%s:%i'%(profile, channel) )
    
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
