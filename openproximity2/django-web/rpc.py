#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import gc
#gc.set_debug(gc.DEBUG_STATS)

from net.aircable.utils import logger, logmain

if __name__ == '__main__':
    logmain('rpc.py')

# setup Django ORM
try:
    import settings # Assumed to be in the same directory.
    setattr(settings, "DEBUG", False)
    logger.info("RPC-DEBUG %s" % getattr(settings, "DEBUG"))
    from django.core.management import setup_environ
    setup_environ(settings)
except ImportError:
    logger.error("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

from net.aircable.openproximity.pluginsystem import pluginsystem
pluginsystem.post_environ()

# now we can safely import the rest
import net.aircable.openproximity.signals as signals
import openproximity.rpc as rpc
import openproximity.rpc.scanner, openproximity.rpc.uploader
import threading, time, traceback, sys

from django.db import transaction, models, close_connection, reset_queries
from openproximity.models import CampaignFile, Setting
from rpyc import Service, async
from rpyc.utils.server import ThreadedServer, ForkingServer

services = set()
pending = set()
enabled = True # useful when tables are been drop
all_dongles = set()

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
	    pending = set()
	    if exit:
		sys.exit(3) # restart me please

	@transaction.commit_manually
	def exposed_listener(self, signal, *args, **kwargs):
	    global enabled
	    
	    if not enabled:
		logger.debug("rpc is locked, dropping signal %s" % signal)
		return
	    
	    logger.debug("exposed_listener %s %s %s" % ( signal, args, kwargs) )
	    kwargs['pending']=pending
	    
	    try:
		for plugin in pluginsystem.get_plugins('rpc'):
		    plugin.provides['rpc'](signal=signal, services=services, manager=self, *args, **kwargs)
		transaction.commit() # commit only after all the plugins have handled
	    except Exception, err:
		logger.error("rpc listener while doing plugins")
		logger.exception(err)
		transaction.rollback() # oops rollback

	    try:	
		if signals.isScannerSignal(signal):
		    rpc.scanner.handle(services, signal, self, *args, **kwargs)
		elif signals.isUploaderSignal(signal):
		    rpc.uploader.handle(services, signal, self, *args, **kwargs)
		transaction.commit() # commit only after scanner and upload has done it's work
	    except Exception, err:
		logger.error("rpc listener while doing scanner or uploader")
		logger.exception(err)
		transaction.rollback() # oops rollback
	    logger.debug("freeing up some memory: %s" % len(gc.garbage))
	    
	    #this things happen when a web request is completed
	    #we don't have a web request, have to do it our own
	    reset_queries()
	    close_connection()
	    del gc.garbage[:]
	    gc.collect()
	    logger.debug("done: %s" % len(gc.garbage))

	def exposed_generic_register(self, remote_quit, dongles, ping, client):
	    logger.info("generic register")
	    all_dongles.update(dongles)
	    try:
		for plugin in pluginsystem.get_plugins('rpc_register'):
			logger.debug("plugin %s provides rpc register" % plugin.name )
			if plugin.provides['rpc_register'](dongles=dongles, client=client):
			    # wrap all calls as async, to avoid collitions
			    self.remote_quit = async(remote_quit)
			    self.ping = ping
			    logger.info("plugin %s handled rpc_register" % plugin.name)
			    return
	    except Exception, err:
		logger.exception(err)

	def exposed_scanner_register(self, remote_quit, scanner, dongles, ping):
	    global enabled
	    all_dongles.update(dongles)
	    self.dongles = set()
	    # wrap all calls as async, to avoid collitions
	    self.add_dongle = async(scanner.add_dongle)
	    self.scanner = scanner
	    self.setConcurrent = async(scanner.setConcurrent)
	    self.refreshScanners = async(scanner.refreshScanners)
	    self.doScan = async(scanner.doScan)
	    self.startScanningCycle = async(scanner.startScanningCycle)
	    self.remote_quit = async(remote_quit)
	    self.ping = ping

	    if not enabled:
		return

	    logger.info("scanner register %s" % dongles)
	    for dongle in dongles:
		self.dongles.add( str(dongle), )

	    for dongle, priority, name in rpc.scanner.get_dongles(dongles): # local
		logger.info("%s: %s [%s]" % (dongle, name, priority) )
		self.add_dongle(dongle, priority, name)

	    (setting, created) = Setting.objects.get_or_create(name="scanner-concurrent") # local

	    concurrent = (created == False and setting.value)

	    logger.info("Concurrent setting %s" % concurrent)
	    self.scanner.setConcurrent(concurrent)
	    self.refreshScanners()

	def exposed_uploader_register(self, remote_quit, uploader, dongles, ping):
	    global enabled
	    all_dongles.update(dongles)
	    self.dongles = set()
	    self.add_dongle = async(uploader.add_dongle)
	    self.upload = async(uploader.upload)
	    self.ping = ping
	    self.remote_quit = async(remote_quit)
	    self.refreshUploaders = async(uploader.refreshUploaders)

	    self.uploader = uploader

	    if not enabled:
		return

	    logger.info("uploader register")
	    for dongle in dongles:
		self.dongles.add( str(dongle), )

	    for dongle, max_conn, name in rpc.uploader.get_dongles(dongles):
		logger.info("%s: %s[%s]" % (dongle, name, max_conn))
		self.add_dongle(dongle, max_conn, name)
	    self.refreshUploaders()

	def exposed_getFile(self, path):
	    logger.info("getFile %s" % path)
	    return CampaignFile.objects.get(file=path).file.read()

	def exposed_getUploadersCount(self):
	    count = 0
	    for ser in services:
		if getattr(ser,'uploader',None) is not None:
		    count += 1
	    logger.info("getUploadersCount %s" % count)
	    return count

	def exposed_getScannersCount(self):
	    count = 0
	    for ser in services:
		if getattr(ser,'scanner',None) is not None:
		    count += 1
	    logger.info("getScannersCount %s" % count)
	    return count

	def exposed_getDongles(self):
	    out=set()

	    for ser in services:
		if ser.dongles is not None:
		    for d in ser.dongles:
			out.add(d,)
	    logger.info("getDongles %s" % out)
	    return list(out)
	    
	def exposed_getAllDongles(self):
	    logger.info("getAllDongles %s" % all_dongles)
	    return list(all_dongles)

	def __str__(self):
	    return str(dir(self))

	def exposed_exit(self):
	    logger.info("remoteExit")
	    return self.exit(True)

	def exposed_restart(self):
	    logger.info("remoteRestart")
	    return self.exit(False)

	def exposed_Lock(self):
	    logger.info("lock requested")
	    global enabled
	    enabled = False
	    self.exit(False)

	def exposed_Unlock(self):
	    logger.info("lock released")
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
