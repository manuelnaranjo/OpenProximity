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
from net.aircable.openproximity.signals import scanner as signals
from openproximity.models import *
from random import random
from re import compile
from rpyc import async
from rpyc.utils.lib import ByValWrapper
from net.aircable.openproximity.pluginsystem import pluginsystem
from net.aircable.utils import logger, trace
import traceback, sys

def is_known_dongle(address, klass):
    return klass.objects.filter(address=address).count() > 0
    
AIRCABLE_MAC=['00:50:C2', '00:25:BF']
ADDRESS_MAC=compile("([0-9A-F]{2}\:){5}([0-9A-F]{2})")

def isAIRcable(address):
    return address[:8].upper() in AIRCABLE_MAC

def get_uploader(services):
    for i in services:
        if getattr(i, 'uploader', None) is not None:
            return i
    return None

def do_upload(uploader, 
                    files, 
                    remote, 
                    service='opp', 
                    dongle_name=None, 
                    channel=None,
                    dongle=None):
    logger.info("do_upload")
    logger.debug("About to call upload")

    uploader.upload(ByValWrapper(files), 
        remote, 
        service, 
        dongle_name=dongle_name, 
        channel=channel,
        uploader=dongle.address if dongle else None)
    logger.debug("upload called async")
    
def get_files_from_campaign(camp, record):
    if camp.hasAccepted(record.remote):
        logger.info("Allready accepted")
        raise StopIteration
        
    c = camp.getRejectedCount(record.remote)
    d = camp.getTimeoutCount(record.remote)

    if c>0 or d>0:
        logger.debug("All ready rejected %s times, and timedout %s" % (c, d))
        try_ = camp.tryAgain(remote=record.remote, record=None)
        logger.info("try again: %s" % try_)
        if not try_ :
            raise StopIteration
            
    files__ = camp.campaignfile_set
    files__ = files__.filter(chance__isnull=True) | files__.filter(
                                        chance__gte=str(random())
    )
    for f in files__:
        logger.debug('going to upload %s' % f.file)
        yield str(f.file.name), camp.pk

def found_action(services, address, record, pending, dongle):
    line = LogLine()
    line.content="Found action for: %s" % address
    try:
        for plugin in pluginsystem.get_plugins('found_action'):
            logger.info("found action trying with %s" % plugin.name)
            service = plugin.rpc['found_action'](services=services, record=record)
            if service:
                logger.info("plugin has handled")
                line.content+=" %s is handling" % getattr(plugin, 'name', 
                                                                    'plugin')
                line.save()
                pending[record.remote.address]=service
                return True
    except Exception, err:
        logger.error("plugin do_action")
        logger.exception(err)

    #fall back to normal uploader
    uploader = get_uploader(services)

    if uploader is None:
        line.content+=" no uploaders, can't handle"
        line.save()
        return True

    logger.info("found uploader")

    camps = getMatchingCampaigns(
            record.remote, 
            enabled=True, 
            record=record, 
            classes=[MarketingCampaign,]
    )


    if len(camps)==0:
        line.content+=" no matching campaings, not handling"
        line.save()
        logger.info("no campaigns")
        return True

    channel = None

    files=list()
    name=None
    service='opp'
    use_same = False

    for camp in camps:
        files.extend( list(get_files_from_campaign(camp, record)) )
        if camp.dongle_name:
            name = camp.dongle_name
        service = camp.get_service_display()
        if camp.fixed_channel and camp.fixed_channel > -1:
          channel = camp.fixed_channel
        if camp.upload_on_discovered:
            use_same = True
    logger.info("going to upload %s files" % len(files))
    if len(files) > 0:
        pending[record.remote.address]=uploader
        do_upload(uploader, files, record.remote.address, service, name, 
                channel=channel, dongle=dongle if use_same else None)
        line.content+=" uploading files"
    else:
        line.content+=" no files to upload"
    
    line.save()

