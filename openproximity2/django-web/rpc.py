#!/usr/bin/env python
#    OpenProximity2.0 is a proximity marketing OpenSource system.
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

import threading, time, traceback, sys

from django.core.management import setup_environ
from rpyc import Service, async
from rpyc.utils.server import ThreadedServer, ForkingServer

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

setup_environ(settings)
from openproximity.models import CampaignFile, Setting
import net.aircable.openproximity.signals as signals
import openproximity.rpc as rpc
import openproximity.rpc.scanner, openproximity.rpc.uploader
from pluginsystem import pluginsystem	

pluginsystem.post_environ()

services = set()
pending = set()

enabled = True # useful when tables are been drop

class OpenProximityService(Service):
	dongles = None
	remote_quit = None
	
	def on_connect(self):
	    services.add(self)
	    
	def on_disconnect(self):
	    services.remove(self)
	    
	def exit(self, exit):
	    for ser in services:
		if ser.remote_quit is not None:
		    try:
			ser.remote_quit()
		    except:
			pass
	    if exit:
		sys.exit(3) # restart me please
	    
	def listener(self, signal, *args, **kwargs):
	    print signal, args, kwargs
	    kwargs['pending']=pending
	    try:
		for plugin in pluginsystem.get_plugins():
		    if plugin.provides.get('rpc', None) is not None:
			plugin.provides['rpc'](signal=signal, services=services, manager=self, *args, **kwargs)
	    except:
		print "ERROR on rpc listener while doing plugins"
		traceback.print_exc(file=sys.stdout)
	    try:	
		if signals.isScannerSignal(signal):
		    rpc.scanner.handle(services, signal, self, *args, **kwargs)
		elif signals.isUploaderSignal(signal):
		    rpc.uploader.handle(services, signal, self, *args, **kwargs)
	    except:
		print "ERROR on rpc listener while doing scanner or uploader"
		traceback.print_exc(file=sys.stdout)    

	def exposed_scanner_register(self, remote_quit, scanner, dongles, ping):
	    global enabled

	    self.dongles = set()
	    # wrap all calls as async, to avoid collitions
	    self.add_dongle = async(scanner.add_dongle)
	    self.scanner = scanner
	    self.setConcurrent = async(scanner.setConcurrent)
	    self.refreshScanners = async(scanner.refreshScanners)
	    self.addListener = async(scanner.addListener)
	    self.doScan = async(scanner.doScan)
	    self.startScanningCycle = async(scanner.startScanningCycle)
	    self.remote_quit = async(remote_quit)
	    self.ping = ping

	    if not enabled:
		return

	    self.addListener(self.listener)

	    for dongle in dongles:
		self.dongles.add( str(dongle), )

	    for dongle, priority, name in rpc.scanner.get_dongles(dongles): # local
		print dongle, priority, name
		self.add_dongle(dongle, priority, name)

	    (setting, created) = Setting.objects.get_or_create(name="scanner-concurrent") # local

	    concurrent = (created == False and setting.value)

	    print "Concurrent setting:", concurrent
	    self.scanner.setConcurrent(concurrent)
	    self.refreshScanners()

	def exposed_uploader_register(self, remote_quit, uploader, dongles, ping):
	    global enabled

	    self.dongles = set()
	    self.add_dongle = async(uploader.add_dongle)
	    self.addListener = async(uploader.addListener)
	    self.upload = async(uploader.upload)
	    self.ping = ping
	    self.remote_quit = async(remote_quit)
	    self.refreshUploaders = async(uploader.refreshUploaders)

	    self.uploader = uploader

	    if not enabled:
		return

	    self.addListener(self.listener)

	    for dongle in dongles:
		self.dongles.add( str(dongle), )

	    for dongle, max_conn, name in rpc.uploader.get_dongles(dongles):
		print dongle, max_conn, name
		self.add_dongle(dongle, max_conn, name)
	    self.refreshUploaders()
	    
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
	
	def exposed_exit(self):
	    return self.exit(True)
	
	def exposed_restart(self):
	    return self.exit(False)
	    
	def exposed_Lock(self):
	    global enabled
	    enabled = False
	    self.exit(False)
	    
	def exposed_Unlock(self):
	    global enabled
	    enabled = True
	    self.exit(False)

def run():
    server=ThreadedServer(OpenProximityService, '0.0.0.0', 
		port=8010, auto_register=False)
    server.start()
    	    
if __name__ == "__main__":
    from net.aircable import autoreload

    autoreload.main(run)
