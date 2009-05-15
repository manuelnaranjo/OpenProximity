#!/usr/bin/env python
from django.core.management import setup_environ
from rpyc import Service, async
from rpyc.utils.server import ThreadedServer
import threading, time
import sys

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

services = set()
pending = set()
	
class OpenProximityService(Service):
	dongles = None
	remote_quit = None
	
	def on_connect(self):
	    services.add(self)
	    
	def on_disconnect(self):
	    services.remove(self)
	    
	def exit(self):
	    for ser in services:
		if ser.remote_quit is not None:
		    try:
			ser.remote_quit()
		    except:
			pass
	    sys.exit(0)
	    
	def listener(self, signal, *args, **kwargs):
	    print signal, args, kwargs
	    kwargs['pending']=pending
	    if signals.isScannerSignal(signal):
		try:
		    rpc.scanner.handle(services, signal, self.scanner, args, kwargs)
		except Exception, err:
		    print err
		    self.exit()
	    elif signals.isUploaderSignal(signal):
		try:
		    rpc.uploader.handle(services, signal, self.uploader, args, kwargs)
		except Exception, err:
		    print err
		    self.exit()
	    else:
		print "not known signal"
	    
	def exposed_scanner_register(self, remote_quit, scanner, dongles):
	    self.dongles = set()
	    self.add_dongle = async(scanner.add_dongle)
	    self.scanner = scanner
	    self.scanner.addListener(self.listener)

	    for dongle in dongles:
		self.dongles.add( str(dongle), )

	    
	    for dongle, priority, name in rpc.scanner.get_dongles(dongles):
		print dongle, priority, name
		self.add_dongle(dongle, priority, name)
	    self.scanner.refreshScanners()
	    print self.dongles
	    
	    self.scanner.startScanningCycle()
	    self.remote_quit = async(remote_quit)

	def exposed_uploader_register(self, remote_quit, uploader, dongles):
	    self.dongles = set()
	    self.add_dongle = async(uploader.add_dongle)
	    self.uploader = uploader
	    self.uploader.addListener(self.listener)

	    for dongle in dongles:
		self.dongles.add( str(dongle), )
	    
	    for dongle, max_conn, name in rpc.uploader.get_dongles(dongles):
		print dongle, max_conn, name
		self.add_dongle(dongle, max_conn, name)
	    self.uploader.refreshUploaders()
	    
	    self.upload = async(self.uploader.upload) # don't want to wait for you
	    
	    self.remote_quit = async(remote_quit)
	    
	def exposed_getFile(self, path):
	    print "getFile", path
	    return CampaignFile.objects.get(file=path).file.read()
	
	def exposed_getUploadersCount(self):
	    count = 0
	    for ser in services:
		if getattr(ser,'uploader',None) is not None:
		    count += 1
	    return count
	    
	def exposed_getScannersCount(self):
	    count = 0
	    for ser in services:
		if getattr(ser,'scanner',None) is not None:
		    count += 1
	    return count
	
	def exposed_getDongles(self):
	    print "getDongles"
	    out=set()
	    
	    for ser in services:
		if ser.dongles is not None:
		    for d in ser.dongles:
			out.add(d,)
	    print "return", out
	    return list(out)
	    
	def __str__(self):
	    return str(dir(self))
	
	def exposed_restart(self):
	    return self.exit()
	    
if __name__ == "__main__":
    setup_environ(settings)
    from openproximity.models import CampaignFile
    import openproximity.signals as signals
    import openproximity.rpc as rpc
    import openproximity.rpc.scanner, openproximity.rpc.uploader
    server=ThreadedServer(OpenProximityService, '0.0.0.0', port=8010, auto_register=False)
    server.start()
