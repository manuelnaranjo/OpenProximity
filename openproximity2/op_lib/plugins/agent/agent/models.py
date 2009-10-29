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

# agent plugin
# defines new clases for db integration

from openproximity.models import DeviceRecord, RemoteDevice, MarketingCampaign
from django.db import models
from django.utils.translation import ugettext as _


#class AgentRemoteDevice(models.Model):
#    ''' A class that wrapps arround a needed to send remote device
#	this class is used to keep a list of needed to send devices
#    '''
#    commited = models.BooleanField(default=False)
#    record = models.OneToOneField(RemoteDevice)
    
#def post_save_remote_device(sender, instance, created, **kwargs):
#    '''creates a new AgentRemoteDevice when a new RemoteDevice is created'''
#    if sender != RemoteDevice or not created:
#	return
#
#    print "new remote device", instance
#    b=AgentRemoteDevice()
#    b.record = instance
#    b.commited = False
#    b.save()
#
#models.signals.post_save.connect(post_save_remote_device)

class AgentDeviceRecord(models.Model):
    ''' A class that wrapps arround a needed to send remote record
	this class is used to keep a list of needed to send records
    '''
    commited = models.BooleanField(default=False)
    record = models.OneToOneField(DeviceRecord)

def valid_classes(model):
    out=(model,)
    if len(model.__subclasses__())>0:
	for submod in model.__subclasses__():
	    out+=valid_classes(submod)
    return out

VALID_CLASSES=valid_classes(DeviceRecord)
def post_save_remote_device_record(sender, instance, created, **kwargs):
    '''creates a new AgentDeviceRecord when a new DeviceRecord is created'''
    #print "post_save_remote_device", sender, instance, created, kwargs
    valid_class = sender==DeviceRecord or sender in VALID_CLASSES
    if not valid_class or not created:
	return
    print "new device_record"
    b=AgentDeviceRecord()
    b.record = instance
    b.save()

models.signals.post_save.connect(post_save_remote_device_record)

class AgentRecord(models.Model):
    commited = models.BooleanField(default=False)
    signal = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    kwargs = models.CharField(max_length=400, blank=True, null=True)

    def __unicode__(self):
	return "%s: %s" % (self.signal, self.kwargs)

try:
    ''' test method to tell if DB needs to be updated '''
    AgentRecord.objects.all().count()
    AgentDeviceRecord.objects.all().count()
#    AgentRemoteDevice.objects.all().count()
except Exception, err:
    if str(err).lower().find('table not') > -1:
	print err
	print 'You need to run syncdb first to init Agent plugin'

class AgentMarketingCampaign(MarketingCampaign):
    hash_id = models.CharField(max_length=100, unique=True)
    last_modification = models.DateField(blank=True, null=True)
