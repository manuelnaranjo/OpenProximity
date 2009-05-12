from openproximity.signals import uploader as signals
from openproximity.models import *

def handle(services, signal, uploader, args, kwargs):
    print "uploader signal", signals.TEXT[signal], args, kwargs
    
    if signal == signals.SDP_RESOLVED:
	handle_sdp_resolved(kwargs['dongle'], kwargs['address'], kwargs['port'])
    elif signal == signals.SDP_NORECORD:
	handle_sdp_norecord(kwargs['dongle'], kwargs['address'], 
	    kwargs['pending'])
    elif signal == signals.SDP_TIMEOUT:
	handle_sdp_timeout(kwargs['dongle'], kwargs['address'], 
	    kwargs['pending'])
    elif signal == signals.FILE_UPLOADED:
	handle_file_uploaded(kwargs['dongle'], kwargs['address'], 
	    kwargs['pending'], kwargs['port'], kwargs['files'])
    elif signal == signals.FILE_FAILED:
	handle_file_failed(kwargs['dongle'], kwargs['address'], 
	    kwargs['pending'], kwargs['port'], kwargs['files'], kwargs['ret'], 
	    kwargs['stderr'], services)
    else:
	print "signal ignored"
    

def get_dongles(dongles):
    out = list()
    
    for address in dongles:
        print address
        try:
    	    dongle = UploaderBluetoothDongle.objects.get(address=address)
            out.append( (address, dongle.max_conn) )
        except Exception, err:
            print err
    return out

def handle_sdp_resolved(dongle, remote, channel):
    print "Valid SDP:", dongle, remote, channel
    record = RemoteBluetoothDeviceSDP()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.channel = channel
    record.setRemoteDevice(remote)
    record.save()

def handle_sdp_norecord(dongle, remote, pending):
    print "No SDP:", dongle, remote
    pending.remove(remote)
    record = RemoteBluetoothDeviceNoSDP()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.setRemoteDevice(remote)
    record.save()
    
def handle_sdp_timeout(dongle, remote, pending):
    print "SDP timeout:", dongle, remote    
    pending.remove(remote)
    record = RemoteBluetoothDeviceSDPTimeout()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.setRemoteDevice(remote)
    record.save()

def handle_file_uploaded(dongle, remote, pending, channel, files):
    print "files uploaded:", dongle, remote, channel, files
    pending.remove(remote)
    record = RemoteBluetoothDeviceFilesSuccess()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.rule = get_campaign_rule(files)
    record.setRemoteDevice(remote)
    record.save()

def handle_file_failed(dongle, remote, pending, channel, files, ret, err, services):
    print dongle, remote, channel, files
    print err
    
    record = RemoteBluetoothDeviceFilesRejected()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    rule = get_campaign_rule(files)
    if rule is None:
	raise Exception("Couldn't find rule")
    record.rule = rule
    record.ret_value = ret
    record.setRemoteDevice(remote)
    record.save()
    
    if record.isTimeout():
	print "timeout"
	for s in services:
	    print "trying again"
	    if getattr(s, 'uploader', None) is not None:
		s.uploader.upload(files, remote)
		return
    else:
	pending.remove(remote)
    print dongle, remote, channel, files, ret
    print err
