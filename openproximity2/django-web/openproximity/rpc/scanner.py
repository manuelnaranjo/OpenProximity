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
from net.aircable.openproximity.signals import scanner as signals
from openproximity.models import *

from rpyc import async
from pickle import loads

from common import get_uploader, do_upload

import time

def handle(services, signal, scanner, args, kwargs):
    print "scanner signal:", signals.TEXT[signal]
    logl = LogLine()
    logl.content += signals.TEXT[signal]

    if signal == signals.DONGLES_ADDED:
	print "Dongles initializated"
	cycle_completed(scanner)
    elif signal == signals.NO_DONGLES:
	print "NO SCANNER DONGLES!!!" 
    elif signal == signals.DONGLE_NOT_AVAILABLE:
	print "DONGLE NOT AVAILABLE", kwargs['address']
	logl.content += " " + kwargs['address']
	do_scan(scanner)
    elif signal == signals.CYCLE_SCAN_DONGLE_COMPLETED:
	print "DONGLE DONE WITH SCAN", kwargs['address']
	logl.content += " " + kwargs['address']
	do_scan(scanner)
    elif signal == signals.CYCLE_COMPLETE:
	cycle_completed(scanner)
    elif signal == signals.CYCLE_START:
	pass
    elif signal == signals.CYCLE_SCAN_DONGLE:
	logl.content += " " + kwargs['address']
	started(scanner, kwargs['address'])
    elif signal == signals.FOUND_DEVICE:
	logl.content += " " + kwargs['address']
	addrecords(services, kwargs['address'], 
	    loads(kwargs['records']), 
	    # this object is pickled so we can get multiple threads
	    # working without locks
	    kwargs['pending'])
    else:
	raise Exception("Not known signal")
    
    logl.save()

def started(scanner, address):
    print 'scan_started', address
    dongle = ScannerBluetoothDongle.objects.get(address=address)
    record = DeviceRecord()
    record.action = signals.CYCLE_SCAN_DONGLE
    record.dongle = dongle
    record.save()

def get_dongles(dongles):
    out = list()
    
    for address in dongles:
	try:
	    dongle = ScannerBluetoothDongle.objects.get(address=address)
	    print "%s is a scanner dongle" % address
	    
	    if dongle.enabled:
		out.append( (address, dongle.priority, dongle.name) )
	    	
	    if dongle.remote_dongles.count() > 0:
		print "We have remote dongles available"
		for remote in dongle.remote_dongles.all():
		    if remote.enabled:
			out.append( (remote.address, remote.priority, dongle.address) )

	except Exception, err:
	    print err
    return out

def do_scan(scanner):
    print "start scan"
    scanner.doScan()

def cycle_completed(scanner):
    print 'scanner_cycle_complete'
    camps = getMatchingCampaigns(enabled=True)
    if len(camps)==0:
	print "no campaigns"
	return
    
    print "starting scan cycle"
    scanner.startScanningCycle()
    scanner.doScan()

uploaded = set()

from random import random

def do_action(services, address, record, pending):
    uploader = get_uploader(services)
    
    if uploader is None:
	return True
	
    print "found uploader"
    camps = getMatchingCampaigns(record.remote, enabled=True)
		    
    if len(camps)==0:
	return True
    
    files=list()
			
    for camp in camps:
	rec = RemoteBluetoothDeviceFilesSuccess.objects.filter( campaign=camp, 
		remote=record.remote)
        if rec.count() > 0:
	    print "Allready accepted"
	    continue
	
	rec = RemoteBluetoothDeviceFilesRejected.objects.filter(campaign=camp, 
	    remote=record.remote).order_by('time')
	if rec.count() > 0:
	    try_ = camp.tryAgain(rec.latest(field_name='time'))
	    print "Allready rejected, try again", try_
	    if not try_ :
		continue
	    	    
	for f in camp.campaignfile_set.all():
	    if f.chance is None or random() <= f.chance:
		print 'going to upload', f.file
		files.append( (str(f.file.name), camp.pk) ,)
    			    
    if len(files) > 0:
	uploaded.add(record.remote.address)
    	pending.add(record.remote.address)
    	do_upload(uploader, files, record.remote.address)

def handle_addrecord(services, remote_, dongle, pending):
    address = remote_['address']

    if RemoteDevice.objects.filter(address=address).count() == 0:
        print 'first time found, not yet known in our DB'
        remote = RemoteDevice()
        remote.address = address
	if remote_['name'] is not None:
    	    remote.name = remote_['name']
    	remote.devclass = remote_['devclass']
        remote.save()
        
    record = RemoteBluetoothDeviceFoundRecord()
    record.action = signals.FOUND_DEVICE
    record.dongle = dongle
    record.setRemoteDevice(address)
    record.setRSSI(remote_['rssi'])

    if record.remote.name is None and remote_['name'] is not None:
        record.remote.name = remote_['name']
        record.remote.save()
    if record.remote.devclass == -1 and remote_['devclass'] != -1:
        record.remote.devclass = remote_['devclass']
        record.remote.save()
	
    record.save()
    
    if address not in pending:
	return do_action(services, address,record, pending)

    return True
    
def addrecords(services, address, records, pending):
    print 'addrecords', address
    dongle = ScannerBluetoothDongle.objects.get(address=address)

    for i in records:
        handle_addrecord(services, i, dongle, pending)

    return True
