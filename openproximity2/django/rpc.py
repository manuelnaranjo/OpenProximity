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
	def on_connect(self):
	    services.add(self)
	    
	def on_disconnect(self):
	    services.remove(self)
	    
	def exit(self):
	    for ser in services:
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
	    self.dongles = dongles
	    self.add_dongle = async(scanner.add_dongle)
	    self.scanner = scanner
	    self.scanner.addListener(self.listener)
	    
	    for dongle, priority in rpc.scanner.get_dongles(dongles):
		print dongle, priority
		self.add_dongle(dongle, priority)
	    self.scanner.refreshScanners()
	    
	    self.scanner.startScanningCycle()
	    self.remote_quit = async(remote_quit)

	def exposed_uploader_register(self, remote_quit, uploader, dongles):
	    self.dongles = dongles
	    self.add_dongle = async(uploader.add_dongle)
	    self.uploader = uploader
	    self.uploader.addListener(self.listener)
	    
	    for dongle, max_conn in rpc.uploader.get_dongles(dongles):
		print dongle, max_conn
		self.add_dongle(dongle, max_conn)
	    self.uploader.refreshUploaders()
	    self.remote_quit = async(remote_quit)
	    
	def exposed_getFile(self, path):
	    print "getFile", path
	    return CampaignFile.objects.get(file=path).file.read()

if __name__ == "__main__":
    setup_environ(settings)
    from openproximity.models import CampaignFile
    import openproximity.signals as signals
    import openproximity.rpc as rpc
    import openproximity.rpc.scanner, openproximity.rpc.uploader
    server=ThreadedServer(OpenProximityService, '0.0.0.0', port=8010, auto_register=False)
    server.start()
