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
from net.aircable.openproximity.signals import scanner as signals
from openproximity.models import *
from random import random
from re import compile
from rpyc import async
from rpyc.utils.lib import ByValWrapper

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

def do_upload(uploader, files, remote, service='opp', dongle_name=None):
    print "About to call upload"
    uploader.upload(ByValWrapper(files), remote, service, dongle_name=dongle_name)
    print "upload called async"

def found_action(services, address, record, pending):
    try:
	
	for plugin in pluginsystem.get_plugins('found_action'):
	    if plugin.provides['found_action'](services, adress, record):
		    pending.add(record.remote.address)
		    return True
    except:
	print "ERROR on plugin do_action"
	traceback.print_exc(file=sys.stdout)

    #fall back to normal uploader
    uploader = get_uploader(services)

    if uploader is None:
	return True

    print "found uploader"
    camps = getMatchingCampaigns(record.remote, enabled=True)

    if len(camps)==0:
	print "no campaigns"
	return True

    files=list()
    name=None
    service='opp'

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

	files__ = camp.campaignfile_set
	files__ = files__.filter(chance__isnull=True) | files__.filter(chance__gte=str(random()))
	for f in files__:
    	    print 'going to upload', f.file
	    files.append( (str(f.file.name), camp.pk) ,)
	if camp.dongle_name:
	    name = camp.dongle_name
	service = camp.get_service_display()

    print len(files), "files"
    if len(files) > 0:
	uploaded.add(record.remote.address)
    	pending.add(record.remote.address)
    	do_upload(uploader, files, record.remote.address, service, name)
    else:
	print "no files"

