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
                setting = settings.GETUPLOADERDONGLE(address)
                if not setting:
                   logger.info('no settings for uploaders')
                   continue

                logger.info('default settings where found')
                logger.debug(setting)
                max_conn = setting.get('value', 1)
                enabled = setting.get('enable', True)
                name = setting.get('name', _("Autodiscovered Bluetooth dongle"))

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
    for camp in get_campaign_rule(files):
        record = RemoteBluetoothDeviceFilesSuccess()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        record.campaign = camp
        record.setRemoteDevice(remote)
        record.save()

def handle_file_failed(dongle, remote, pending, channel, files, ret, err, services):
    logger.info("handle file failed %s[%s]: %s" % (remote, channel, files))
    logger.debug(err)
    try:
        record = RemoteBluetoothDeviceFilesRejected()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        rule = get_campaign_rule(files)
        if rule is None:
            raise Exception("Couldn't find rule")
        record.campaign = rule
        record.ret_value = ret
        record.setRemoteDevice(remote)
        record.save()
        
        # from here we try again either on timeout or if rejected count is 
        # smaller than filter
        try_again = rule.tryAgain(record)
        
        logger.info("try again: %s" % try_again)
        if try_again:
            uploader = get_uploader(services)
            if uploader:
                logger.info("trying again")
                return do_upload(uploader, files, remote)
            else:
                logger.info("no uploader registered")
    except Exception, err:
        logger.error("OOOPS!!!")
        logger.exception(err)
    logger.info("taking out of pending list")
    pending.pop(remote)

