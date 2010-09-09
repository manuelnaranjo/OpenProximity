# -*- coding: utf-8 -*-
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

from django.db import transaction
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _
from models import *
from serverxr import CameraManager
from openproximity.models import getMatchingCampaigns
from re import compile
from rpyc import async
from net.aircable.utils import logger, trace
from utils import isAIRcable
from threading import Thread
import signals
import time

import unicodedata, re

all_chars = (unichr(i) for i in xrange(0x110000))
# or equivalently and much more efficiently
control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))

control_char_re = re.compile('[%s]' % re.escape(control_chars))

def remove_control_chars(s):
    return control_char_re.sub('', s)

clients = dict()
handlers = dict()
service = dict()
''' a dict holding when each device was last time served '''

def handle(signal, services, manager, *args, **kwargs):
    if not signals.isCameraSignal(signal):
	return
    global handlers

    logger.info("Camera HANDLE %s %s %s" % (signals.TEXT[signal], args, kwargs) )

    if signal in handlers:
	return handlers[signal](manager=manager, *args, **kwargs)

    logger.error("Camera, no handler %s" % signals.TEXT[signal])

def get_dongles(dongles):
    return CameraBluetoothDongle.objects.filter(address__in=dongles, enabled=True).\
	values_list('address', 'max_conn')

class Client:
    def __init__(self, client):
	self.client=client
	self.add_dongle=async(client.add_dongle)
	self.refreshDongles=async(client.refreshDongles)
	self.connect=async(client.connect)
	self.setZoneMinderBackend = async(client.setZoneMinderBackend)
	self.setOpenProximityBackend = async(client.setOpenProximityBackend)

def register(client=None, dongles=None):
    logger.info("register  %s %s" % (client, dongles))
    if repr(client).find('camera.serverxr.CameraManager') == -1:
        logger.debug("no match")
        return False

    client=Client(client)
    dongles = get_dongles(list(dongles))

    for dongle, max_conn in dongles:
        clients[dongle]=client
        client.add_dongle(dongle, max_conn)

    client.refreshDongles()
    return True

TIMEOUT=60

def check_if_service(address):
    clean_service()
    if address in service:
	if time.time()-service[address] < TIMEOUT:
	    logger.info("has served in less than %s seconds" % TIMEOUT)
	    return False

    latest=CameraRemoteDevice.objects.filter(address=address)

    if latest.count() > 0 and time.time() - \
	time.mktime(latest.latest('latest_served').latest_served.timetuple()) < TIMEOUT:
	logger.info("has served in less than %s seconds" % TIMEOUT)
	return False
    return True

def clean_service():
    for addr, val in service.copy().iteritems():
	if time.time() - val > TIMEOUT:
	    logger.info("more than %s seconds had happend since last time %s was served" % (TIMEOUT, addr))
	    service.pop(addr)


def found_action(record, services):
    dongle = record.dongle.address
    logger.info("camera device_found %s: %s[%s]" % (dongle , record.remote.address, record.remote.name))
    camps = getMatchingCampaigns(record.remote, enabled=True, classes=[CameraCampaign,])
    if len(camps) == 0:
	return False
    if len(camps) > 1:
	e = Exception("There's more than one campaign that matches, check settings")
	logger.exception(e)
	raise e

    logger.debug("found campaign")
    camp = camps[0]
    
    global clients
    if clients.get(dongle, None) is None:
	logger.debug("dongle not registered as client")
	logger.debug(clients)
	logger.debug(dongle)
	return False # there's no registered service I can't do a thing

    address = record.remote.address
    if not check_if_service(address):
	return False

    latest = CameraRemoteDevice.objects.filter(address=address)
    if latest.count() > 0:
	for k in latest.all():
	    k.save() # mark elements as served, so timeout can exist

    service[address] = time.time()

    logger.info("handling device %s" % address)
    client = clients[dongle]

    client.setZoneMinderBackend(camp.enable_zm)
    client.setOpenProximityBackend(camp.use_backend)
    client.connect(record.remote.address)
    logger.debug("connecting")
    return client

def handle_picture(picture=None, target=None, dongle=None, pending=None, 
	*args, **kwargs):
    try:
	dongle = CameraBluetoothDongle.objects.get(address=dongle)
	remote, created = CameraRemoteDevice.objects.get_or_create(
	    address=target,
	    defaults = {'name':_('Generic Camera')}
	)
	remote.save()
	record = CameraRecord()
	record.dongle = dongle
	record.remote = remote
	record.picture.save(
	    "%s_%s.jpg" % (target.replace(':', ''), time.time()), 
	    ContentFile(picture)
	)
        record.save()
    except Exception, err:
	logger.exception(err)

def work_done(pending, target, *args, **kwargs):
    logger.info("disconnected %s" % target)
    pending.pop(target)

def handle_failed(pending, target, *args, **kwargs):
    logger.error("handle failed %s" % target)
    pending.pop(target)

handlers[signals.HANDLE_OK]=work_done
handlers[signals.HANDLE_PICTURE]=handle_picture
handlers[signals.DISCONNECTED]=handle_failed
handlers[signals.TOO_BUSY]=handle_failed
handlers[signals.CONNECTION_FAILED]=handle_failed
handlers[signals.HANDLE_LOST_CONNECTION]=handle_failed
