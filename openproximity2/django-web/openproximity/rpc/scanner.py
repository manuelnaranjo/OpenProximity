from openproximity.signals import scanner as signals
from openproximity.models import *

def handle(services, signal, scanner, args, kwargs):
    print "scanner signal:", signals.TEXT[signal], args, kwargs	

    if signal == signals.DONGLES_ADDED:
	print "Dongles initializated"
	cycle_completed(scanner)
    elif signal == signals.NO_DONGLES:
	print "NO SCANNER DONGLES!!!" 
	return 1
    elif signal == signals.CYCLE_COMPLETE:
	cycle_completed(scanner)
    elif signal == signals.CYCLE_START:
	return 0
    elif signal == signals.CYCLE_SCAN_DONGLE:
	started(scanner, kwargs['address'])
    elif signal == signals.FOUND_DEVICE:
	addrecords(services, kwargs['address'], kwargs['records'], kwargs['pending'])
    else:
	raise Exception("Not known signal")

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
	print address
	try:
	    dongle = ScannerBluetoothDongle.objects.get(address=address, enabled=True)
	    out.append( (address, dongle.priority, dongle.name) )
	except Exception, err:
	    print err
    return out

def cycle_completed(scanner):
    print 'scanner_cycle_complete', scanner
    camps = getMatchingCampaigns()
    if len(camps)>0:
	print "starting scan cycle"
	scanner.startScanningCycle(False)
    else:
	print "no campaigns"

uploaded = set()

from random import random

def addrecords(services, address, records, pending):
    print 'addrecords', address, records
    dongle = ScannerBluetoothDongle.objects.get(address=address)

    for i in records:
        address = i['address']
        print address

        if len(RemoteDevice.objects.filter(address=address)) == 0:
            print 'first time found, not yet known in our DB'
            remote = RemoteDevice()
            remote.address = i['address']
            remote.name = i['name']
            remote.devclass = i['devclass']
            print "saving", remote.devclass
            remote.save()
        
        record = RemoteBluetoothDeviceFoundRecord()
    	record.action = signals.FOUND_DEVICE
    	record.dongle = dongle
    	record.setRemoteDevice(address)
    	record.setRSSI(i['rssi'])
    	record.save()
        
        if address not in pending: # in case we discover the same device more than once while still serving
    	    for i in services:
    		if getattr(i, 'uploader', None) is not None:
    		    print "found uploader"
    		    camps = getMatchingCampaigns(record.remote)
    		    
    		    if len(camps)>0: #and len(RemoteBluetoothDeviceFileTry.objects.filter(remote__address=record.remote.address)) == 0:
    			files=list()
    			uploaded.add(record.remote.address)
    			pending.add(record.remote.address)

    			for camp in camps:
    			    print camp
			    for f in camp.rules.files.all():
    				print f
    				if f.chance is None or random() <= f.chance:
    				    print f.file
    				    files.append( (str(f.file.name), camp.pk) ,)
    			    
    			    i.upload(files, record.remote.address) # async call
