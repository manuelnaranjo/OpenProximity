# -*- coding: utf-8 -*-
import dbus
import dbus.glib
import gobject

    
def ping():
    try:
	server.ping()
	return True
    except:
	print "lost connection"
	loop.quit()


def init():
    print "init"
    
    type = sys.argv[3].lower()

    a=list()
    for b in manager.manager.ListAdapters():
	obj = bus.get_object('org.bluez', b)
	adapter = dbus.Interface(obj, 'org.bluez.Adapter')
    	a.append(str(adapter.GetProperties()['Address']))

    
    if type == 'scanner':
	server.root.scanner_register(loop.quit, manager, a)
    elif type == 'uploader':
	server.root.uploader_register(loop.quit, manager, a)
    
    print "exiting init"
	
    return False

if __name__ == '__main__':
	# connect to server
	import sys
	if len(sys.argv) < 4:
	    print "usage: %s server-ip port type" % sys.argv[0]
	    sys.exit(0)
	    
	from utils import settings, logger
	import rpyc
	
	bus=dbus.SystemBus()
	gobject.threads_init()
	dbus.glib.init_threads()

	type_ = sys.argv[3].lower()

	server = rpyc.connect(sys.argv[1], int(sys.argv[2]))
	if type_ == 'scanner':
	    from scanner import ScanManager
	    print "init scanner"
	    manager = ScanManager(bus)
	elif type_ == 'uploader':
    	    print "init uploader"
	    from uploader import UploadManager
	    manager = UploadManager(bus, rpc=server)
	else:
	    print "not valid type use either scanner or uploader by now"
	    sys.exit(0)

	gobject.timeout_add(100, init) # delay initialization 'til loop is running
	gobject.timeout_add(1000, ping)
	
	loop=gobject.MainLoop()
	print "loop"
        loop.run()
