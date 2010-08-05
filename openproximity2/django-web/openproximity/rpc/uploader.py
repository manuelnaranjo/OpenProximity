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
from django.utils.translation import ugettext as _
from net.aircable.openproximity.signals import uploader as signals
from net.aircable.utils import logger
from openproximity.models import *

from common import get_uploader, do_upload, is_known_dongle, isAIRcable

#from pickle import loads

import traceback

SET = settings.OPENPROXIMITY

def handle(services, signal, uploader, *args, **kwargs):
    logger.info("uploader signal: %s" % signals.TEXT[signal])
    logl = LogLine()
    logl.content += signals.TEXT[signal]
    
    if signal == signals.SDP_RESOLVED:
        logl.content += ' %s:%s' %( kwargs['address'], kwargs['port'])
        handle_sdp_resolved(
                kwargs['dongle'], 
                kwargs['address'], 
                kwargs['port']
        )
    elif signal == signals.SDP_NORECORD:
        logl.content += ' %s' %( kwargs['address'])
        handle_sdp_norecord(
                kwargs['dongle'], 
                kwargs['address'], 
                kwargs['pending']
        )
        
    elif signal == signals.SDP_TIMEOUT:
        logl.content += ' %s' %( kwargs['address'])
        handle_sdp_timeout(
            kwargs['dongle'], 
            kwargs['address'], 
            kwargs['pending'])
    elif signal == signals.FILE_UPLOADED:
        logl.content += ' %s' %( kwargs['address'])
        handle_file_uploaded(
            kwargs['dongle'], 
            kwargs['address'], 
            kwargs['pending'], 
            kwargs['port'], 
            kwargs['files'])
    elif signal == signals.FILE_FAILED:
        logl.content += ' %s, ret:%s' %( kwargs['address'], kwargs['ret'])
        handle_file_failed(
                kwargs['dongle'], 
                kwargs['address'], 
                kwargs['pending'], 
                kwargs['port'], 
                kwargs['files'], 
                kwargs['ret'], 
                kwargs['stderr'], 
                services)
    else:
        logger.error("signal ignored")
    
    logl.save()

def get_dongles(dongles):
    out = list()
    
    for address in dongles:
        print address
        try:
            if not is_known_dongle(address, UploaderBluetoothDongle) and \
                                                            isAIRcable(address):
                logger.info('not known uploader %s' % address)
                settings = SET.getSettingsByAddress(address)
                if not 'uploader' in settings:
                   logger.info('no settings for uploaders')
                   continue
                    
                logger.info('default settings where found')
                logger.debug(settings['uploader'])
                max_conn = settings['uploader'].get('max_conn', 1)
                enabled = settings['uploader'].get('enable', True)
                name = settings['uploader'].get('name', _("Autodiscovered Bluetooth dongle"))
                    
                UploaderBluetoothDongle.objects.get_or_create(address=address, 
                    defaults={
                        'name': name,
                        'enabled': enabled,
                        'max_conn': max_conn
                    }
                )
            dongle = UploaderBluetoothDongle.objects.get(address=address, enabled=True)
            out.append( (address, dongle.max_conn, dongle.name) )
        except Exception, err:
            logger.exception(err)
    return out

def handle_sdp_resolved(dongle, remote, channel):
    logger.info("Valid SDP: %s %s" % (remote, channel) )
    remote=RemoteDevice.objects.filter(address=remote).get()
    if RemoteBluetoothDeviceSDP.objects.filter(remote=remote).count() == 0:
        logger.info("New SDP result")
        record = RemoteBluetoothDeviceSDP()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        record.channel = channel
        record.remote = remote
        record.save()

def handle_sdp_norecord(dongle, remote, pending):
    logger.info("No SDP: %s" % remote)
    pending.pop(remote)
    remote=RemoteDevice.objects.filter(address=remote).get()
    if RemoteBluetoothDeviceNoSDP.objects.filter(remote=remote).count() == 0:
        record = RemoteBluetoothDeviceNoSDP()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        record.remote = remote
        record.save()
    
def handle_sdp_timeout(dongle, remote, pending):
    logger.info("SDP timeout: %s" % remote )
    pending.pop(remote)
    record = RemoteBluetoothDeviceSDPTimeout()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.setRemoteDevice(remote)
    record.save()

def handle_file_uploaded(dongle, remote, pending, channel, files):
    logger.info("files uploaded: %s[%s]: %s" % ( remote, channel, files) )
    pending.pop(remote)
    for rule in get_campaign_rule(files):
	record = RemoteBluetoothDeviceFilesSuccess()
	record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
	record.campaign = rule
	record.setRemoteDevice(remote)
	record.save()

def get_files_from_campaign(camp):
    files__ = camp.campaignfile_set

    for f in files__:
	logger.debug('going to upload %s' % f.file)
        yield str(f.file.name), camp.pk 

def upload_after_rejected(rules, services):
    if len(rules) == 0:
	raise Exception("no need to try again")
    
    uploader = get_uploader(services)
    if not uploader:
	raise Exception("No uploader, can't try again")
    
    logger.info("trying again")
    files = set()
    
    for rule in rules:
	files.extend( list(get_files_from_campaign(rule, record)) )
    
    do_upload(uploader, files, remote)
    return True

def save_file_failed(rule, dongle, ret, remote):
    record = RemoteBluetoothDeviceFilesRejected()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.campaign = rule
    record.ret_value = ret
    record.setRemoteDevice(remote)
    record.save()
    return record

def handle_file_failed(dongle, remote, pending, channel, files, ret, err, services):
    logger.info("handle file failed %s[%s]: %s" % (remote, channel, files))
    logger.debug(err)
    try:
        try_again = []
	rules = get_campaign_rule(files)
        if rules is None or len(rules)==0:
            raise Exception("Couldn't find rule")

        for rule in rules:
            save_file_failed(rule, dongle, ret, remote)

    	    # from here we try again either on timeout or if rejected count is 
    	    # smaller than filter
    	    if rule.tryAgain(record):
    		try_again.append(rule)

	# if we can't try again this method will raise an exception
	# and the try/catch will make sure the remote device gets out
	# of our pending list
        if upload_after_rejected(try_again, services):
    	    return
    except Exception, err:
        logger.error("OOOPS!!!")
        logger.exception(err)
    logger.info("taking out of pending list")
    pending.pop(remote)

