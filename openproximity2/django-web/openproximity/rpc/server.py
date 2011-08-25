#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   OpenProximity2.0 is a proximity marketing OpenSource system.
#   Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation version 2 of the License.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import gc
from net.aircable.utils import logger, logmain
from net.aircable.openproximity.pluginsystem import pluginsystem
import net.aircable.openproximity.signals as signals
import scanner, uploader
import threading, time, traceback, sys

from django.db import transaction, close_connection, reset_queries
from openproximity.models import CampaignFile, getMatchingCampaigns, \
    RemoteDevice
from rpyc import Service, async
from rpyc.utils.server import ThreadedServer, ForkingServer
from dispatcher import Dispatcher

services = set()
pending = dict()
enabled = True # useful when tables are been drop
all_dongles = set()

def db_ready():
    try:
        from openproximity.models import BluetoothDongle
        BluetoothDongle.objects.count()
        return True
    except Exception, err:
        logger.info("Database not ready")
        logger.exception(err)
        return False

class OpenProximityService(Service):
    dongles = None
    remote_quit = None
    instance = None

    def __init__(self, *args, **kwargs):
        logger.info("New OpenProximityServer")
        Service.__init__(self, *args, **kwargs)
        OpenProximityService.instance = self

    def on_connect(self):
        services.add(self)

    def on_disconnect(self):
        a = [ p for p in pending if pending[p]==self]
        if len(a) > 0:
           logger.info("a client disconnected, clearing %s pending transactions" % len(a))
           for p in a:
               pending.pop(p)
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
                plugin.rpc['handle'](
                    signal=signal, 
                    services=services, 
                    manager=self, 
                    *args, **kwargs)
            transaction.commit() 
            # commit only after all the plugins have handled
        except Exception, err:
            logger.error("rpc listener while doing plugins")
            logger.exception(err)
            transaction.rollback() # oops rollback

        try:
            if signals.isScannerSignal(signal):
                scanner.handle(services, signal, self, *args, **kwargs)
            elif signals.isUploaderSignal(signal):
                uploader.handle(services, signal, self, *args, **kwargs)
            transaction.commit()
            # commit only after scanner and upload has done it's work
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

    def exposed_generic_register(self, remote_quit=None, 
            dongles=None, client=None):
        logger.info("generic register")

        all_dongles.update(dongles)

        if not enabled:
            return

        if not db_ready():
            return

        try:
            for plugin in pluginsystem.get_plugins('rpc_register'):
                logger.debug("plugin %s provides rpc register" % 
                    plugin.name)
                if plugin.rpc['register'](dongles=dongles, client=client):
                    # wrap all calls as async, to avoid collitions
                    self.remote_quit = async(remote_quit)
                    logger.info("plugin %s handled rpc_register" % 
                        plugin.name)
                    return
        except Exception, err:
            logger.exception(err)

    def exposed_scanner_register(self,  client = None,
            remote_quit=None, dongles=None):
        global enabled
        all_dongles.update(dongles)
        self.dongles = set()
        # wrap all calls as async, to avoid collitions
        self.add_dongle = async(client.add_dongle)
        self.scanner = client
        self.setConcurrent = async(client.setConcurrent)
        self.refreshScanners = async(client.refreshScanners)
        self.doScan = async(client.doScan)
        self.startScanningCycle = async(client.startScanningCycle)
        self.remote_quit = async(remote_quit)
        self.noCampaigns = async(client.noCampaigns)

        if not enabled:
            return

        if not db_ready():
            return

        logger.info("scanner register %s" % dongles)
        for dongle in dongles:
            self.dongles.add( str(dongle), )

        for dongle, priority, name in scanner.get_dongles(dongles): # local
            logger.info("%s: %s [%s]" % (dongle, name, priority) )
            self.add_dongle(dongle, priority, name)
        self.refreshScanners()

    def exposed_uploader_register(self, client = None,
            remote_quit=None, dongles=None):
        global enabled
        all_dongles.update(dongles)
        self.dongles = set()
        self.add_dongle = async(client.add_dongle)
        self.upload = async(client.upload)
        self.remote_quit = async(remote_quit)
        self.refreshUploaders = async(client.refreshUploaders)

        self.uploader = client

        if not enabled:
            return

        if not db_ready():
            return

        logger.info("uploader register")
        for dongle in dongles:
            self.dongles.add( str(dongle), )

        for dongle, max_conn, name in uploader.get_dongles(dongles):
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
        return count

    def exposed_getScannersCount(self):
        count = 0
        for ser in services:
            if getattr(ser,'scanner',None) is not None:
                count += 1
        return count

    def exposed_getDongles(self):
        def getDongles_internal(self):
            for ser in services:
                if ser.dongles is not None:
                    for d in ser.dongles:
                        yield d

        return set(getDongles_internal(self))

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

    def exposed_getPIN(self, remote, local):
        logger.info("getPIN request for %s->%s" % (local, remote) )
        remote = RemoteDevice.getRemoteDevice(address=remote)
        try:
            for camp in getMatchingCampaigns(remote=remote, enabled=True)
                if not camp.pin_code:
                    continue
                logger.debug("pin code: %s" % camp.pin_code)
                return camp.pin_code
        except Exception, err:
            logger.error(err)
            logger.exception(err)
        logger.info("No pin code")

        raise Exception("No pin code found")
