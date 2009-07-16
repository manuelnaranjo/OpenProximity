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
from datetime import datetime
import time

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.dispatch.dispatcher import Signal

import rpyc

import net.aircable.openproximity.signals.scanner as scanner

TIMEOUT_RET = [ 22 ]

class BluetoothDongle(models.Model):
    address = models.CharField(max_length=17, 
	blank=False,
	verbose_name=_("bluetooth address"))
    name = models.CharField(max_length=100, blank=True,
	verbose_name=_("identifying name"))
    enabled = models.BooleanField()
    position_x = models.DecimalField(null=True, blank=True, decimal_places=2,
	max_digits=10, help_text=_("location on field of dongle"))
    position_y = models.DecimalField(null=True, blank=True, decimal_places=2,
	max_digits=10, help_text=_("location on field of dongle"))

    def enabled_display(self):
	if self.enabled:
	    return "Enabled"
	return "Disabled"
    
    def __unicode__(self):
	return "%s - %s, %s" % (self.address, self.name, self.enabled_display() )


class ScannerBluetoothDongle(BluetoothDongle):
    priority = models.IntegerField()
    
    def __unicode__(self):
	return "Scanner: %s, %s" % (BluetoothDongle.__unicode__(self), 
	    self.priority)
	    
class RemoteScannerBluetoothDongle(ScannerBluetoothDongle):
    local_dongle = models.ForeignKey(ScannerBluetoothDongle, 
	related_name="remote_dongles" )

class UploaderBluetoothDongle(BluetoothDongle):
    max_conn = models.IntegerField(default=7,
	verbose_name=_("connections"),
	help_text=_("maximum allowed connections"))
	
    def __unicode__(self):
	return "Uploader: %s, %s" % (BluetoothDongle.__unicode__(self), 
	    self.max_conn)

class SensorSDKBluetoothDongle(BluetoothDongle):
    channels = models.IntegerField(default=4,
	help_text='amount of records to create')
    channel_desc = models.CharField(
	default="SensorSDK SPP channel",
	verbose_name = "Channel description",
	max_length=100) 

SERVICE_TYPES = (
    (0,	  u'opp'),
    (1,	  u'ftp'),
    (3,	  u'spp'),
)

class CampaignFile(models.Model):
    chance = models.DecimalField(null=True, blank=True, default=1.0, decimal_places=2, max_digits=3,
	help_text=_("if < 1 then a random number generator will check if the user is lucky enough to get this file"))
    file = models.FileField(upload_to='campaign',
	help_text=_("campaign file itself"))
    
    def __unicode__(self):
	return "%s: %.2f" % (self.file, self.chance)


class CampaignRule(models.Model):
    name_filter = models.CharField(null=True, max_length=10, blank=True,
	verbose_name=_("name filter"))
    addr_filter = models.CharField(null=True, max_length=10, blank=True,
	verbose_name=_("address filter"))
    devclass_filter = models.IntegerField(null=True, blank=True)
    service = models.IntegerField(default=0, choices=SERVICE_TYPES)
    rejected_count = models.IntegerField(default=2,
	help_text=_("how many times it should try again when rejected, -1 infinte"))
    tries_count = models.IntegerField(default=-1,
	help_text=_("how many times it should try to send when timing out, -1 infinite"))
    start = models.DateTimeField(null=True, blank=True,
	help_text=_("starting date, or null to run for ever until end"))
    end = models.DateTimeField(null=True, blank=True,
	help_text=_("ending date, or null to run for ever since start"))
    files = models.ManyToManyField(CampaignFile)
	
    def __unicode__(self):
	out = ""
	if self.name_filter is not None and len(self.name_filter):
	    out += "%s, " % self.name_filter
	else:
	    out += "*, "
	    
	if self.addr_filter is not None and len(self.addr_filter):
	    out += "%s, " % self.addr_filter
	else:
	    out += "*, "

	out += "%s, " % self.get_service_display()
	
	if self.start is not None:
	    out += "%s, " % self.start
	else:
	    out += "*, "

	if self.end is not None:
	    out += "%s, " % self.end
	else:
	    out += "*, "
	
#	if self.files.count() > 0:
#	    out+="\nfiles: "
#	    for file in self.files.all():
#		out+="%s, " % file.__unicode__()
	return out.strip()[:-1]
	
    def tryAgain(self, record):
	if record.isTimeout():
	    print "Timeout"
	    if self.tries_count == -1:
		print "No timeout filter"
		return True
	    return RemoteBluetoothDeviceFileTry. \
		filter(remote=record.remote). \
		count() < self.tries_count
	else:
	    print "Rejected"
	    if self.rejected_count == -1:
		print "No rejection filter"
		return True
	    return RemoteBluetoothDeviceFilesRejected. \
		filter(remote=record.remote). \
		count() < self.rejected_count

CampaignFile.rules = models.ManyToManyField(CampaignRule)

class MarketingCampaign(models.Model):
    #name is going to change
    friendly_name = models.CharField(max_length=100)
    rules = models.ForeignKey(CampaignRule)
    
    enabled = models.BooleanField()
    
    def __unicode__(self):
	return self.friendly_name

class RemoteDevice(models.Model):
    address = models.CharField(max_length=17, 
	blank=False,
	verbose_name=_("bluetooth address"))
    name = models.CharField(max_length=100, blank=True, null=True,
	verbose_name=_("identifying name"))
    last_seen = models.DateTimeField(auto_now=True, blank=False,
	verbose_name=_("time"))
    devclass = models.IntegerField(null=True)
    
    def __unicode__(self):
	return "%s, %s" % (self.address, self.name)
	
class SensorSDKRemoteDevice(RemoteDevice):
    sensor = models.CharField(max_length=32, 
	blank=False,
	verbose_name=_("kind of sensor attached"))
    mode = models.CharField(max_length=32, 
	blank=False,
	verbose_name=_("working mode"))

    def __unicode__(self):
	return "%s, %s, %s, %s" % (self.address, self.name, self.sensor, 
	    self.mode)

class DeviceRecord(models.Model):
    time = models.DateTimeField(auto_now=True, blank=False,
	verbose_name=_("time"))
    dongle = models.ForeignKey(BluetoothDongle, blank=True, null=True,
	verbose_name=_("dongle address"))

    def __unicode__(self):
	return self.dongle.address

class RemoteBluetoothDeviceRecord(DeviceRecord):
    remote = models.ForeignKey(RemoteDevice, verbose_name=_("remote address"))

    def setRemoteDevice(self, address):
	try:
	    self.remote=RemoteDevice.objects.get(address=address)
	except Exception, err:
	    print err
    
    def __unicode__(self):
	return "%s, %s" % (
	    self.dongle.address, 
	    self.remote.address
	)

class RemoteBluetoothDeviceFoundRecord(RemoteBluetoothDeviceRecord):
    __rssi = models.CommaSeparatedIntegerField(max_length=200, verbose_name=_("rssi"))

    def setRSSI(self, rssi):
	self.__rssi = str(rssi).replace('[','').replace(']','')
	
    def getRSSI(self):
	return [ int(a) for a in self.__rssi.split(",") ]

    def __unicode__(self):
	return "%s, %s, %s" % (
	    self.dongle.address, 
	    self.remote.address,
	    self.__rssi)

class RemoteBluetoothDeviceSDP(RemoteBluetoothDeviceRecord):
    channel = models.IntegerField(help_text=_("bluetooth rfcomm channel that provides the used service"))
    
    def __unicode__(self):
	return "%s, %s, %s" % (
	    self.remote.address,
	    self.remote.name, 
	    self.channel
	)

# this comes from http://code.google.com/p/django-geo/source/browse/trunk/fields.py?r=13#49
class DictionaryField(models.Field):
        # Django seems to do some funky stuff prohibiting this class from inheriting from
        # PickledObjectField which I can't be bothered to explore. This is quicker, but not DRY :-(
        __metaclass__ = models.SubfieldBase
        
        def to_python(self, value):
                if isinstance(value, dict):
                        return value
                else:
                        if not value:
                                return value
                        return pickle.loads(str(value))
        
        def get_db_prep_save(self, value):
                if value is not None and not isinstance(value, basestring):
                        if isinstance(value, dict):
                                value = pickle.dumps(value)
                        else:
                                raise TypeError('This field can only store dictionaries. Use PickledObjectField to store a wide(r) range of data types.')
                return value
        
        def get_internal_type(self): 
                return 'TextField'
        
        def get_db_prep_lookup(self, lookup_type, value):
                if lookup_type == 'exact':
                        value = self.get_db_prep_save(value)
                        return super(DictionaryField, self).get_db_prep_lookup(lookup_type, value)
                elif lookup_type == 'in':
                        value = [self.get_db_prep_save(v) for v in value]
                        return super(DictionaryField, self).get_db_prep_lookup(lookup_type, value)
                else:
                        raise TypeError('Lookup type %s is not supported.' % lookup_type)

# end of http://code.google.com/p/django-geo/source/browse/trunk/fields.py?r=13#49

class RemoteSensorSDKDeviceRecord(DeviceRecord):
    remote_device = models.ForeignKey(SensorSDKRemoteDevice)
    extra = DictionaryField()
    campaign = models.ForeignKey(MarketingCampaign)

class RemoteBluetoothDeviceNoSDP(RemoteBluetoothDeviceRecord):
    pass

class RemoteBluetoothDeviceSDPTimeout(RemoteBluetoothDeviceRecord):
    pass

class RemoteBluetoothDeviceFileTry(RemoteBluetoothDeviceRecord):
    rule = models.ForeignKey(CampaignRule)
    
class RemoteBluetoothDeviceFilesRejected(RemoteBluetoothDeviceFileTry):
    ret_value = models.IntegerField()
    
    def isTimeout(self):
	return self.ret_value is not None and self.ret_value in TIMEOUT_RET
	
    def __unicode__(self):
	return "%s %s" % (RemoteBluetoothDeviceFileTry.__unicode__(self), self.ret_value)

class RemoteBluetoothDeviceFilesSuccess(RemoteBluetoothDeviceFileTry):
    pass

def getMatchingCampaigns(remote=None, 
	    time_=datetime.fromtimestamp(time.time()), 
	    enabled=None):
    print "getMatchingCampaigns", time_
    out  = list()
    
    rules = CampaignRule.objects
    
    if enabled is not None:
	rules = rules.filter(marketingcampaign__enabled=enabled)
    
    rules=rules.all()
    
    for rule in rules:
	if rule.start is None or time_ >= rule.start: 
	    # if it's not none then rule.start holds a value we can compare
	    print 'start matches'
	    if rule.end is None or time_ <= rule.end:
		print 'end matches'
		if remote is None:
		    out.append(rule.marketingcampaign_set.get())
		else:
		    if rule.name_filter is None or remote.name.startswith(rule.name_filter):
			print "name filter matches"
			if rule.addr_filter is None or remote.address.startswith(rule.addr_filter):
			    print "address filter matches"
		    	    print remote.devclass, rule.devclass_filter
			    if rule.devclass_filter is None or (remote.devclass & rule.devclass_filter)>0:
				print "devclass filter matches"
				out.append(rule.marketingcampaign_set.get())
    return out

def get_campaign_rule(files):
    print 'get_campaign_rule', files
    out = set()

    for file, camp_id in files:
	print file
        try:
	    camp = CampaignRule.objects.get(pk=camp_id)
    	    print camp
            if len(out) > 0 and camp not in out:
                print "multiple return values"
            out.add(camp)
        except Exception, err:
            print err
    if len(out) == 0:
        return None

    return list(out)[0]

def __restart_server():
    print "restarting server"
    try:
	server = rpyc.connect('localhost', 8010)
	server.root.restart()
    except:
	#could be that we're only running the web server
	pass
    

def bluetooth_dongle_signal(instance, **kwargs):
    ''' gets called when ever there is a change in dongles '''
    if type(instance) in [ BluetoothDongle, ScannerBluetoothDongle, 
	    UploaderBluetoothDongle, SensorSDKBluetoothDongle ]:
        print 'bluetooth_dongle_signal'
	__restart_server()

def campaign_signal(instance, **kwargs):
    ''' gets called when ever there is a change in marketing campaigns '''
    if type(instance) in [ CampaignRule, CampaignFile, MarketingCampaign ]:
	print 'campaing_signal'
	__restart_server()

models.signals.post_save.connect(bluetooth_dongle_signal)
models.signals.post_save.connect(campaign_signal)
