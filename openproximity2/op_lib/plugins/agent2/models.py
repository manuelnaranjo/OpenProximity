#	OpenProximity2.0 is a proximity marketing OpenSource system.
#	Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation version 2 of the License.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License along
#	with this program; if not, write to the Free Software Foundation, Inc.,
#	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


# test plugin
# defines new clases for db integration

from openproximity.models import DeviceRecord
import openproximity.models as mod
from django.db import models
from django.db.models.signals import post_save
from functools import partial

class uploadFoundRecord(models.Model):
    '''
    A simple class that connects to a remote bluetooth device found record
    to tell if it needs to be uploaded or not, there's a flag to avoid
    collisions
    '''
    record = models.ForeignKey(mod.RemoteBluetoothDeviceFoundRecord)
    flag = models.BooleanField(default=False)
    fields = ('record__remote__address', 'record___rssi', 'record__time') 
    
    # class variable
    apiurl = "api/foundrecords/"

    @classmethod
    def values_to_dict(klass, values):
	return [{
	    'address': x[0], 
	    'rssi': x[1], 
	    'time': x[2]
	} 
	for x in values]

class uploadSDPRecord(models.Model):
    '''
    A simple class that connects to a remote bluetooth device found record
    to tell if it needs to be uploaded or not, there's a flag to avoid
    collisions
    '''
    record = models.ForeignKey(mod.RemoteBluetoothDeviceSDP)
    flag = models.BooleanField(default=False)
    fields = ('record__remote__address', 'record__channel', 'record__time', 'service')
    service = models.CharField(
	choices=(('NN','NN'), 
		    ('opp','opp'),
		    ('ftp','ftp')),
	max_length=3, 
	default='NN')

    apiurl = "api/sdprecords/"

    @classmethod
    def values_to_dict(klass, values):
	return [{
	    'address': x[0], 
	    'channel': x[1], 
	    'time': x[2],
	    'service': x[3]
	} 
	for x in values]

class UploadRecord(models.Model):
    '''
    A simple class that lets us log the commited transfers
    '''
    time = models.DateTimeField(auto_now=True)
    commited_scan_records = models.IntegerField()
    commited_sdp_records = models.IntegerField()
    success = models.BooleanField(default=False)

try:
    ''' test method to tell if DB needs to be updated '''
    NeedToUploadRecord.objects.all().count()
except Exception, err:
    if str(err).lower().find('table not') > -1:
	print err
	print 'You need to run syncdb first to init Agent2 plugin'

def handler(klass, sender, instance, created, extra_action=None, 
					*args, **kwargs):
    if created:
	rec = klass(record=instance, flag=False)

	if extra_action:
	    extra_action(rec)
	rec.save()

def resolve_service(rec):
    service='NN'
    rec.record.getAverageRSSI=lambda x: 0
    camps=mod.getMatchingCampaigns(
	rec.record.remote,
	enabled=True,
	classes=[mod.MarketingCampaign,],
	record=rec.record
    )

    for camp in camps:
	service=camp.get_service_display()
    rec.service=service

post_save.connect(partial(handler, klass=uploadFoundRecord),
		weak=False, sender=mod.RemoteBluetoothDeviceFoundRecord)
post_save.connect(partial(handler, 
			    klass=uploadSDPRecord, 
			    extra_action=resolve_service),
		weak=False, sender=mod.RemoteBluetoothDeviceSDP)

def patchRemoteBluetoothDeviceFoundRecord():
    from openproximity.models import RemoteBluetoothDeviceFoundRecord as target
    try:
	target._meta.get_field('_rssi')
	return
    except:
	pass

    print "Monkey Patching RemoteBluetoothDeviceFoundRecord"
    def getRSSI(self):
	return [ int(a) for a in self._rssi.split(",") ]

    def setRSSI(self, rssi):
	self._rssi = str(rssi).replace('[','').replace(']','')

    def __unicode__(self):
        return "%s, %s, %s" % (
    	    self.dongle.address, 
            self.remote.address,
            self._rssi
        )

    field = target._meta.get_field(
	    '_RemoteBluetoothDeviceFoundRecord__rssi')
    field.attname='_rssi'
    field.db_colum='_RemoteBluetoothDeviceFoundRecord__rssi'
    field.name='_rssi'
    i = 0
    for f in target._meta.local_fields:
	if f==field:
	    break;
	i+=1
    del target._meta.local_fields[i]
    target._meta.add_field(field)
    target.getRSSI=getRSSI
    target.setRSSI=setRSSI
    target.__unicode__=__unicode__

patchRemoteBluetoothDeviceFoundRecord()

