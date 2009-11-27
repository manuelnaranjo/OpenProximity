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

from pickle import dumps, loads
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.dispatch.dispatcher import Signal

import rpyc

import net.aircable.openproximity.signals.scanner as scanner

from net.aircable.fields import PickledField

TIMEOUT_RET = [ 22 ]

class LogLine(models.Model):
    time = models.DateTimeField(auto_now=True, verbose_name=_("time"))
    content = models.CharField(max_length=255)

class Setting(models.Model):
    name = models.CharField(max_length=40)
    value = PickledField(max_length=200)

class BluetoothDongle(models.Model):
    address = models.CharField(max_length=17, 
	blank=False, verbose_name=_("bluetooth address"))
    name = models.CharField(max_length=100, blank=True,
	verbose_name=_("identifying name"))
    enabled = models.BooleanField()

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

SERVICE_TYPES = (
    (0,	  u'opp'),
    (1,	  u'ftp'),
)

class Campaign(models.Model):
    #name is going to change
    name = models.CharField(max_length=100)    
    enabled = models.BooleanField(default=True)
    name_filter = models.CharField(null=True, max_length=10, blank=True,
	verbose_name=_("name filter"))
    addr_filter = models.CharField(null=True, max_length=10, blank=True,
	verbose_name=_("address filter"))
    devclass_filter = models.IntegerField(null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True,
	help_text=_("starting date, or null to run for ever until end"))
    end = models.DateTimeField(null=True, blank=True,
	help_text=_("ending date, or null to run for ever since start"))
    dongle_name=models.CharField(null=True, blank=True, max_length=100,
	verbose_name=_("dongles names"),
	help_text=_("if you want your campaign to change the bluetooth dongles names when running then set this variable")
    )
    
    def matches(self, remote, *args, **kwargs):
	return False

    def __unicode__(self):
	return self.name

    class Meta:
	# don't create a table for me please
	abstract = True
	ordering = ['start', 'end', 'name']

class MarketingCampaign(Campaign):
    service = models.IntegerField(default=0, choices=SERVICE_TYPES)
    rejected_count = models.IntegerField(default=2,
	help_text=_("how many times it should try again when rejected, -1 infinite"))
    rejected_timeout = models.IntegerField(default=-1,
	help_text=_("how much time to wait after a certain device has rejected a file before we try again"))
    tries_count = models.IntegerField(default=-1,
	help_text=_("how many times it should try to send when timing out, -1 infinite"))
    tries_timeout = models.IntegerField(default=0,
	help_text=_("how much time to wait after a certain device has made a timeout before we try again"))
    accepted_count = models.IntegerField(default=-1,
	help_text=_("how many times will this campaign be accepted before disabling, -1 means infinite"))
    rssi_min = models.IntegerField(null=True,
	help_text=_("if the meassured rssi is over or equal than this value then campaign will match, take into account rssi is negative, range -255 0"))
    rssi_max = models.IntegerField(null=True,
	help_text=_("if the meassured rssi is less or equal than this value then campaign will match, take into account rssi is negative, range -255 0"))

    def __unicode__(self):
	return "MarketingCampaign: %s" % self.name

    def tryAgain(self, record):
	delta = time.time()-time.mktime(record.time.timetuple())

	if record.isTimeout():
	    print "Timeout"
	    return delta >= self.tries_timeout and (self.tries_count==-1 or \
		    self.tries_count > RemoteBluetoothDeviceFileTry.\
		    objects.filter(remote=record.remote, campaign=record.campaign).count())
	else:
	    print "Rejected"
	    return delta >= self.rejected_timeout and (self.rejected_count==-1 or \
		self.rejected_count > RemoteBluetoothDeviceFilesRejected.\
		objects.filter(remote=record.remote).count())
	
    def matches(self, remote, record=None, *args, **kwargs):
	if self.name_filter is None or remote.name is None or remote.name.startswith(self.name_filter):
	    if self.addr_filter is None or remote.address.startswith(self.addr_filter):
		if self.devclass_filter is None or (remote.devclass & self.devclass_filter)>0:
		    # do RSSI check
		    if record is None or not hasattr(record, getAverageRSSI):
			return True
		    
		    rssi = record.getAverageRSSI()
		    if self.rssi_min is None or rssi > self.rssi_min:
			if self.rssi_max is None or rssi < self.rssi_max:
			    return True
	return False


class CampaignFile(models.Model):
    chance = models.DecimalField(null=True, blank=True, default=1.0, decimal_places=2, max_digits=3,
	help_text=_("if < 1 then a random number generator will check if the user is lucky enough to get this file"))
    file = models.FileField(upload_to='campaign',
	help_text=_("campaign file itself"))
    
    campaign = models.ForeignKey(MarketingCampaign)
    
    def __unicode__(self):
	return "%s: %.2f" % (self.file, self.chance)

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

class DeviceRecord(models.Model):
    time = models.DateTimeField(blank=False, serialize = True,
	verbose_name=_("time"))
    dongle = models.ForeignKey(BluetoothDongle, blank=True, null=True, serialize = True,
	verbose_name=_("dongle address"))

    def __unicode__(self):
	return self.dongle.address
	
    class Meta:
	# don't create a table for me please
#	abstract = True
	ordering = ['time']

    def save(self, force_insert=False, force_update=False):
	if self.time is None:
	    self.time = datetime.now()
	
	super(DeviceRecord, self).save(force_insert, force_update)


class RemoteBluetoothDeviceRecord(DeviceRecord):
    remote = models.ForeignKey(RemoteDevice, verbose_name=_("remote address"), serialize = True)
    
    def setRemoteDevice(self, address):
        qs = RemoteDevice.objects.filter(address=address)
        if qs.count() > 1:
    	    for i in qs[:1]:
    		i.delete()
	self.remote=qs[0]
    
    def __unicode__(self):
	return "%s, %s" % (
	    self.dongle.address, 
	    self.remote.address
	)
	
    class Meta:
	# don't create a table for me please
#	abstract = True
	ordering = ['time']

class RemoteBluetoothDeviceFoundRecord(RemoteBluetoothDeviceRecord):
    __rssi = models.CommaSeparatedIntegerField(max_length=200, verbose_name=_("rssi"), serialize = True)

    def setRSSI(self, rssi):
	self.__rssi = str(rssi).replace('[','').replace(']','')
	
    def getRSSI(self):
	return [ int(a) for a in self.__rssi.split(",") ]

    def getAverageRSSI(self):
	rssi=self.getRSSI()
	return sum(rssi)/float(len(rssi))

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

class RemoteBluetoothDeviceNoSDP(RemoteBluetoothDeviceRecord):
    pass

class RemoteBluetoothDeviceSDPTimeout(RemoteBluetoothDeviceRecord):
    pass

class RemoteBluetoothDeviceFileTry(RemoteBluetoothDeviceRecord):
    campaign = models.ForeignKey(MarketingCampaign)
    
    class Meta:
	# don't create a table for me please
#	abstract = True
	ordering = ['time']
    
class RemoteBluetoothDeviceFilesRejected(RemoteBluetoothDeviceFileTry):
    ret_value = models.IntegerField()
    
    def isTimeout(self):
	return self.ret_value is not None and self.ret_value in TIMEOUT_RET
	
    def __unicode__(self):
	return "%s %s" % (RemoteBluetoothDeviceFileTry.__unicode__(self), self.ret_value)

class RemoteBluetoothDeviceFilesSuccess(RemoteBluetoothDeviceFileTry):

    def save(self, force_insert=False, force_update=False):
	super(RemoteBluetoothDeviceFilesSuccess, self).save(force_insert, force_update)
	if self.campaign.accepted_count > -1:
	    print "accepted filter", self.campaign.accepted_count
	    qs = RemoteBluetoothDeviceFilesSuccess.objects.filter(campaign=self.campaign)
	    print qs.count()
	    if qs.count() >= self.campaign.accepted_count:
		self.campaign.enabled = False
		self.campaign.no_restart = True
		self.campaign.save()

def getMatchingCampaigns(remote=None, time_=None,
	    enabled=None, classes=None, record=None):
    out  = list()

    if classes is None:
	classes = Campaign.__subclasses__()
    if time_ is None:
	time_=datetime(*time.localtime()[:-2])

    for model in classes:
	print model
        rules = model.objects

	if enabled is not None:
	    rules = rules.filter(enabled=enabled)

	rules = rules.all()
	rules = rules.filter(start__isnull=True) | rules.filter(start__lte=time_)
	rules = rules.filter(end__isnull=True) | rules.filter(end__gte=time_)

	if remote is None:
	    out.append(rules)
	    continue

	for rule in rules:
	    if rule.matches(remote, record):
		out.append(rule)

    return out

def get_campaign_rule(files):
    print 'get_campaign_rule', files
    out = set()

    for file, camp_id in files:
	print file
        try:
	    camp = MarketingCampaign.objects.get(pk=camp_id)
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
	    UploaderBluetoothDongle, RemoteScannerBluetoothDongle ]:
        print 'bluetooth_dongle_signal'
	__restart_server()

def campaign_signal(instance, **kwargs):
    ''' gets called when ever there is a change in marketing campaigns '''
    if type(instance) in [ CampaignFile, MarketingCampaign ] and not hasattr(instance, 'no_restart'):
	print 'campaing_signal'
	__restart_server()

models.signals.post_save.connect(bluetooth_dongle_signal)
models.signals.post_save.connect(campaign_signal)
