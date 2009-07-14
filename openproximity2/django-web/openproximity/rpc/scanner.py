from net.aircable.openproximity.signals import scanner as signals
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
	    
	    if dongle.remote_dongles.count() > 0:
		print "We have remote dongles available"
		for remote in dongle.remote_dongles.all():
		    out.append( (remote.address, remote.priority, dongle.address) )

	except Exception, err:
	    print err
    return out

def cycle_completed(scanner):
    print 'scanner_cycle_complete', scanner
    camps = getMatchingCampaigns(enabled=True)
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

        if RemoteDevice.objects.filter(address=address).count() == 0:
            print 'first time found, not yet known in our DB'
            remote = RemoteDevice()
            remote.address = i['address']
	    if i['name'] is not None:
        	remote.name = i['name']
    	    remote.devclass = i['devclass']
            
	    print "saving", remote.devclass
            remote.save()
        
        record = RemoteBluetoothDeviceFoundRecord()
    	record.action = signals.FOUND_DEVICE
    	record.dongle = dongle
    	record.setRemoteDevice(address)
    	record.setRSSI(i['rssi'])
	
	if record.remote.name is None and i['name'] is not None:
	    record.remote.name = i['name']
	    record.remote.save()
	if record.remote.devclass == -1 and i['devclass'] != -1:
	    record.remote.devclass = i['devclass']
	    record.remote.save()
	
    	record.save()
        
        if address not in pending: # in case we discover the same device more than once while still serving
    	    for i in services:
    		if getattr(i, 'uploader', None) is not None:
    		    print "found uploader"
    		    camps = getMatchingCampaigns(record.remote, enabled=True)
		    
    		    if len(camps)>0:
    			files=list()
			
    			for camp in camps:
			    if RemoteBluetoothDeviceFilesSuccess.objects.filter( 
				rule=camp.rules, 
				remote=record.remote).count() > 0:
				print "Allready accepted"
				continue
			    
			    if RemoteBluetoothDeviceFilesRejected.objects.filter( 
				rule=camp.rules, 
				remote=record.remote).count() > 0:
				print "Allready rejected"
				continue
			    
			    for f in camp.rules.files.all():
    				if f.chance is None or random() <= f.chance:
    				    print f.file
    				    files.append( (str(f.file.name), camp.pk) ,)
    			    
			if len(files) > 0:
			    uploaded.add(record.remote.address)
    			    pending.add(record.remote.address)				
    			    i.upload(files, record.remote.address) # async call
