# -*- coding: utf-8 -*-
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from net.aircable.openproximity.signals import scanner as signals
from net.aircable.utils import getLogger
logger = getLogger(__name__)
from openproximity.models import *
from rpyc import async
from common import found_action, is_known_dongle

import time

def handle(signal, *args, **kwargs):
    logger.info("scanner signal: %s" % signals.TEXT[signal])
    logl = LogLine()
    logl.content += signals.TEXT[signal]

    if signal == signals.DONGLES_ADDED:
        logger.info("Dongles initializated")
        cycle_completed()
    elif signal == signals.NO_DONGLES:
        logger.error("NO SCANNER DONGLES!!!")
    elif signal == signals.DONGLE_NOT_AVAILABLE:
        logger.error("DONGLE NOT AVAILABLE %s" % kwargs['address'])
        logl.content += " " + kwargs['address']
        do_scan()
    elif signal == signals.CYCLE_SCAN_DONGLE_COMPLETED:
        logger.info("DONGLE DONE WITH SCAN %s" % kwargs['address'])
        logl.content += " " + kwargs['address']
        do_scan()
    elif signal == signals.CYCLE_COMPLETE:
        cycle_completed()
    elif signal == signals.CYCLE_START:
        pass
    elif signal == signals.CYCLE_SCAN_DONGLE:
        logl.content += " " + kwargs['address']
        started(kwargs['address'])
    elif signal == signals.FOUND_DEVICE:
        logl.content += " " + kwargs['address']
        addrecords(kwargs['address'], 
            kwargs['records']
        )
    else:
        logger.error("unknown signal")
        raise Exception("Not known signal")
    
    logl.save()

def started(address):
    logger.info('scan_started %s' % address)
    dongle = ScannerBluetoothDongle.objects.get(address=address)
    record = DeviceRecord()
    record.action = signals.CYCLE_SCAN_DONGLE
    record.dongle = dongle
    record.save()

def get_dongles(dongles):
    def create_new_discovered_dongle(address, settings):
        logger.info("going to setup as scanner")
        priority = settings.get('value', 1)
        enabled = settings.get('enable', True)
        name = settings.get('name', _("Auto Discovered Dongle"))
        obj, created = ScannerBluetoothDongle.objects.get_or_create(
            address=address, 
            defaults={
                'priority': priority,
                'enabled': enabled,
                'name': name
            })
        logger.debug("%s %s[%s]" % (address, name, priority))

    def internal_get_dongles(address):
        dongle = ScannerBluetoothDongle.objects.get(address=address)
        logger.info("%s is a scanner dongle" % address)
            
        if dongle.enabled:
            yield (address, dongle.priority, dongle.name)
                
        if dongle.remote_dongles.count() > 0:
            logger.info("We have remote dongles available")
            for remote in dongle.remote_dongles.all():
                if remote.enabled:
                    yield ( remote.address, remote.priority, dongle.address )

    out = list()
    
    for address in dongles:
        try:
            if not is_known_dongle(address, ScannerBluetoothDongle):
                logger.info("dongle not known yet %s" % address)
                setting = settings.GETSCANNERDONGLE(address)
                if setting:
                    create_new_discovered_dongle(address, setting)
            out.extend(internal_get_dongles(address))
        except Exception, err:
            logger.exception(err)
    return out

def do_scan():
    from openproximity.rpc.server import OpenProximityService
    logger.info("start scan")
    scanner = OpenProximityService.getScanner()
    scanner.doScan()

def cycle_completed():
    from openproximity.rpc.server import OpenProximityService
    logger.info("scanner_cycle_complete")
    camps = getMatchingCampaigns(enabled=True)
    scanner = OpenProximityService.getScanner()
    if len(camps)==0:
        logger.info("no campaigns, no more scanning")
        # tell the rpc scanner to ping us periodically until there's
        # a new campaign available
        scanner.noCampaigns()
        return

    concurrent = False
    for camp in camps:
        if camp.concurrent_scanning:
            concurrent = True
            break

    logger.info("starting scan cycle")
    scanner.setConcurrent(concurrent)
    scanner.startScanningCycle()
    scanner.doScan()

uploaded = set()

def handle_addrecord(remote_, dongle):
    from openproximity.rpc.server import OpenProximityService
    address = remote_['address']
    name = smart_unicode(remote_['name']) if remote_['name'] else None

    logger.info("handle_addrecord %s" % address)
    remote=RemoteDevice.getRemoteDevice(
        address=address, 
        name=name, 
        devclass=remote_['devclass']
    )
    record = RemoteBluetoothDeviceFoundRecord()
    record.action = signals.FOUND_DEVICE
    record.dongle = dongle
    record.remote = remote
    record.remote.save() # update last seen
    record.setRSSI(remote_['rssi'])
    
    if not isinstance(dongle, RemoteScannerBluetoothDongle):
        if name is not None and record.remote.name!=name:
            record.remote.name = name
            record.remote.save()
        if remote_['devclass'] != -1 and \
                    record.remote.devclass!=remote_['devclass']:
            record.remote.devclass = remote_['devclass']
            record.remote.save()

    logger.debug(record)
    logger.debug(record.remote)

    record.save() # this will set the time field to now
    
    logl = LogLine()
    logl.content="Found: %s %s %s" % (
        record.remote.address, 
        record.remote.name,
        record.getRSSI())
    logl.save()
    
    if not OpenProximityService.isPending(address):
        return found_action(address, record, dongle=dongle)

    return True
    
def addrecords(address, records):
    logger.info('addrecords for dongle %s' % address)
    try:
        dongle = RemoteScannerBluetoothDongle.objects.get(address=address)
        logger.info("remote dongle")
    except:
        logger.info("local dongle")
        dongle = ScannerBluetoothDongle.objects.get(address=address)    

    for i in records:
        handle_addrecord(i, dongle)

    return True

