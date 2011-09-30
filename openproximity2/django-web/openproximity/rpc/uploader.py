# OpenProximity2.0 is a proximity marketing OpenSource system.
# Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
from django.conf import settings
from django.utils.translation import ugettext as _
from net.aircable.openproximity.signals import uploader as signals
from net.aircable.utils import getLogger
logger = getLogger(__name__)
from openproximity.models import *

from common import do_upload, is_known_dongle, isAIRcable, found_action

#from pickle import loads

import traceback

def handle(signal, *args, **kwargs):
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
                kwargs['address'])
        
    elif signal == signals.SDP_TIMEOUT:
        logl.content += ' %s' %( kwargs['address'])
        handle_sdp_timeout(
            kwargs['dongle'],
            kwargs['address'])
    elif signal == signals.FILE_UPLOADED:
        logl.content += ' %s' %( kwargs['address'])
        handle_file_uploaded(
            kwargs['dongle'],
            kwargs['address'],
            kwargs['port'],
            kwargs['files'])
    elif signal == signals.FILE_FAILED:
        logl.content += ' %s, ret:%s' %( kwargs['address'], kwargs['ret'])
        handle_file_failed(
                kwargs['dongle'],
                kwargs['address'],
                kwargs['port'],
                kwargs['files'],
                kwargs['ret'],
                kwargs['stderr'])
    elif signal == signals.PAIR_SUCCESS:
        handle_paired(kwargs['dongle'], kwargs['address'])
    elif signal in [signals.PAIR_TIMEOUT, signals.PAIR_REJECT]:
        handle_pair_error(kwargs['dongle'], kwargs['address'], kwargs['reason'],
            kwargs['exception'])
    else:
        logger.error("signal ignored")
    
    logl.save()

def get_dongles(dongles):
    out = list()
    
    for address in dongles:
        logger.debug(address)
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
    from openproximity.rpc.server import OpenProximityService
    logger.info("Valid SDP: %s %s" % (remote, channel) )
    remote=RemoteDevice.objects.filter(address=remote).get()
    if RemoteBluetoothDeviceSDP.objects.filter(remote=remote).count() == 0:
        logger.info("New SDP result")
        record = RemoteBluetoothDeviceSDP()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        record.channel = channel
        record.remote = remote
        record.save()
    logger.info("Starting bonding process")
    uploader = OpenProximityService.getUploader()
    uploader.start_pairing(remote.address)

def handle_sdp_norecord(dongle, remote):
    logger.info("No SDP: %s" % remote)
    
    from openproximity.rpc.server import OpenProximityService
    OpenProximityService.removePending(remote)

    remote=RemoteDevice.objects.filter(address=remote).get()
    if RemoteBluetoothDeviceNoSDP.objects.filter(remote=remote).count() == 0:
        record = RemoteBluetoothDeviceNoSDP()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        record.remote = remote
        record.save()

def handle_sdp_timeout(dongle, remote):
    logger.info("SDP timeout: %s" % remote )

    from openproximity.rpc.server import OpenProximityService
    OpenProximityService.removePending(remote)

    record = RemoteBluetoothDeviceSDPTimeout()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.setRemoteDevice(remote)
    record.save()

def handle_paired(dongle, remote):
    logger.info("Paired with %s on %s" % (dongle, remote))
    
    record = RemoteBluetoothDevicePairing()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.setRemoteDevice(remote)
    record.state = RemoteBluetoothDevicePairing.STATES["Passed"]
    record.save()
    found_action(remote, dongle=dongle, record=record)

def handle_pair_error(dongle, remote, msg, exception):
    logger.info("Paired failed %s on %s, %s:%s" % (dongle, remote, msg,
        exception))
    
    record = RemoteBluetoothDevicePairing()
    record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
    record.setRemoteDevice(remote)
    if 'reject' in exception.lower():
        record.state = RemoteBluetoothDevicePairing.STATES["Rejected"]
    else:
        record.state = RemoteBluetoothDevicePairing.STATES["Timeout"]
    record.msg = msg
    record.exception = exception
    record.save()
    
    from openproximity.rpc.server import OpenProximityService
    OpenProximityService.removePending(remote)

def handle_file_uploaded(dongle, remote, channel, files):
    logger.info("files uploaded: %s[%s]: %s" % ( remote, channel, files) )

    from openproximity.rpc.server import OpenProximityService
    OpenProximityService.removePending(remote)

    for camp in get_campaign_rule(files):
        record = RemoteBluetoothDeviceFilesSuccess()
        record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
        record.campaign = camp
        record.setRemoteDevice(remote)
        record.save()

def handle_file_failed(dongle, remote, channel, files, ret, err):
    logger.info("handle file failed %s[%s]: %s" % (remote, channel, files))
    logger.debug(err)
    try:
        rules = get_campaign_rule(files)
        if rules is None:
            raise Exception("No matching rule for files %s!" % files)
        record = None
        try_again = False

        for rule in get_campaign_rule(files):
            record = RemoteBluetoothDeviceFilesRejected()
            record.dongle = UploaderBluetoothDongle.objects.get(address=dongle)
            record.campaign = rule
            record.ret_value = ret
            record.setRemoteDevice(remote)
            record.save()
            # from here we try again either on timeout or if rejected count is 
            # smaller than filter, for any of the matching rules
            # if only 1 campaign matches we do it all over!
            try_again = try_again | rule.tryAgain(record)

        logger.info("try again: %s" % try_again)
        if try_again:
            from openproximity.rpc.server import OpenProximityService
            uploader = OpenProximityService.getUploader()
            if uploader:
                logger.info("trying again")
                return do_upload(uploader, files, remote)
            else:
                logger.info("no uploader registered")
    except Exception, err:
        logger.error("OOOPS!!!")
        logger.exception(err)
    logger.info("taking out of pending list")

    from openproximity.rpc.server import OpenProximityService
    OpenProximityService.removePending(remote)
