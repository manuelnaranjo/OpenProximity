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
from datetime import datetime
import time

from pickle import dumps, loads
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.dispatch.dispatcher import Signal
import rpyc, time, os.path

import net.aircable.openproximity.signals.scanner as scanner

from net.aircable.fields import PickledField
from net.aircable.utils import logger

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
        return "%s - %s, %s" % (
                self.address, 
                self.name, 
                self.enabled_display() 
        )

class ScannerBluetoothDongle(BluetoothDongle):
    priority = models.IntegerField()
    
    def __unicode__(self):
        return "Scanner: %s, %s" % (
                BluetoothDongle.__unicode__(self), 
                self.priority
        )
        
class RemoteScannerBluetoothDongle(ScannerBluetoothDongle):
    local_dongle = models.ForeignKey(ScannerBluetoothDongle, 
    related_name="remote_dongles" )

class UploaderBluetoothDongle(BluetoothDongle):
    max_conn = models.IntegerField(default=7,
    verbose_name=_("connections"),
    help_text=_("maximum allowed connections"))
    
    def __unicode__(self):
        return "Uploader: %s, %s" % (
                        BluetoothDongle.__unicode__(self), 
                        self.max_conn
        )

SERVICE_TYPES = (
    (0,   u'opp'),
    (1,   u'ftp'),
)

class Campaign(models.Model):
    #name is going to change
    name = models.CharField(max_length=100)    
    enabled = models.BooleanField(default=True)
    name_filter = models.CharField(
                            null=True,
                            max_length=30,
                            blank=True,
                            verbose_name=_("name filter")
    )
    addr_filter = models.CharField(
                            null=True, 
                            max_length=20, 
                            blank=True,
                            verbose_name=_("address filter")
    )
    devclass_filter = models.IntegerField(null=True, blank=True)
    start = models.DateTimeField(
                            null=True, 
                            blank=True,
                            help_text=_("starting date, or null to run for ever"
                                " until end")
    )
    end = models.DateTimeField(
                            null=True, 
                            blank=True,
                            help_text=_("ending date, or null to run for ever " 
                                "since start")
    )
    dongle_name=models.CharField(
                            null=True, 
                            blank=True, 
                            max_length=100,
                            verbose_name=_("dongles names"),
                            help_text=_("if you want your campaign to change "
                                "the bluetooth dongles names when running then "
                                "set this variable")
    )
    pin_code=models.CharField(
                            null=True, 
                            blank=True, 
                            max_length=16,
                            default="1234",
                            help_text=_("certain target devices require pairing"
                                ", this is the pin code going to be used")
    )
    fixed_channel=models.IntegerField(
			    null=True,
			    blank=True,
			    default = None,
			    help_text=_("if you set this parameter then "
		  "OpenProximity will never try to resolve sdp records and "
		  "use only this channel, leave it empty unless you know "
		  "what you're doing.")
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
    rejected_count = models.IntegerField(
                            default=2,
                            help_text=_("how many times it should try again "
                                        "when rejected, -1 infinite")
    )
    rejected_timeout = models.IntegerField(
                            default=-1,
                            help_text=_("how much time to wait after a certain "
                                        "device has rejected a file before we "
                                        "try again")
    )
    tries_count = models.IntegerField(
                            default=-1,
                            help_text=_("how many times it should try to send "
                                "when timing out, -1 infinite")
    )
    tries_timeout = models.IntegerField(
                            default=0,
                            help_text=_("how much time to wait after a certain "
                                "device has made a timeout before we try again")
    )
    accepted_count = models.IntegerField(
                            default=-1,
                            help_text=_("how many times will this campaign be "
                                "accepted before disabling, -1 means infinite")
    )
    rssi_min = models.IntegerField(
                            null=True, 
                            blank=True,
                            help_text=_("if the meassured rssi is over or equal"
                                " than this value then campaign will match, "
                                "take into account rssi is negative, range -255 "
                                "0")
    )
    rssi_max = models.IntegerField(
                            null=True, 
                            blank=True,
                            help_text=_("if the meassured rssi is less or equal"
                                " than this value then campaign will match, "
                                "take into account rssi is negative, range -255"
                                " 0")
    )


    def __unicode__(self):
        return "MarketingCampaign: %s" % self.name

    def getTimeoutCount(self, remote):
	''' this function will count how many times a certain devices did a
	    timeout
	'''
	return RemoteBluetoothDeviceFilesRejected.objects.\
                filter(remote=remote, campaign=self).\
                filter(ret_value__in=TIMEOUT_RET).count()

    def getRejectedCount(self, remote):
	''' this function will count how many time the user has rejected'''
	return RemoteBluetoothDeviceFilesRejected.objects.\
                filter(remote=remote, campaign=self).\
                exclude(ret_value__in=TIMEOUT_RET).count()
                
    def getTriesCount(self, remote):
	return RemoteBluetoothDeviceFileTry.\
                objects.filter(remote=record.remote, campaign=self).\
                    count()

    def hasAccepted(self, remote):
	return RemoteBluetoothDeviceFilesSuccess.objects.filter(
                campaign=self,
                remote=remote).count()>0
                
    def getAcceptedCount(self):
	return RemoteBluetoothDeviceFilesSuccess.\
	    objects.\
		filter(campaign=self).\
		    count()

    def tryAgain(self, record=None, remote=None):
	assert record or remote, "Can't pass both record and remote as none"

	if not record:
	    qs = RemoteBluetoothDeviceFilesRejected.\
		    objects.\
			filter(
			    campaign=self,
			    remote=remote
			).\
		    order_by('-time')
	    if qs.count() == 0:
		logger.info("first time ever")
		return True

	    record=qs.all()[0]
	    logger.debug("got record, %s" % record)

        delta = time.mktime(time.gmtime())-time.mktime(record.time.timetuple())
        logger.info("delta: %s" % delta)

        if record.isTimeout():
            logger.info("record timeout")
            return delta >= self.tries_timeout and (
		self.tries_count==-1 or \
		self.tries_count > self.getTriesCount(record.remote)
	    )
        else:
            logger.info("record rejected")
            return delta >= self.rejected_timeout and \
                (self.rejected_count==-1 or 
		    self.rejected_count > self.getRejectedCount(record.remote)
		)
    
    def matches(self, remote, record=None, *args, **kwargs):
	'''
	    This function will get called to ask the campaign
	    if it matches the definition rules
	'''
	logger.info("matches %s", self.pk)
	
	# test is we reached the rejected count
	rejected_pass = remote is None or (
	    self.rejected_count == 1 or 
	    self.getRejectedCount(remote) < self.rejected_count
	)
	
	logger.debug("rejected_pass %s" % rejected_pass)
	if not rejected_pass:
	    return False
	
	# test for successful uploads
	accepted_pass = self.accepted_count == -1 or (
	    self.accepted_count > self.getAcceptedCount()
	)
	logger.debug("accepted_pass %s" % accepted_pass)
	if not accepted_pass:
	    return False

	name_pass = self.name_filter is None or \
	    remote.name is None or \
            remote.name.startswith(self.name_filter)
        logger.debug("name_pass: %s" % name_pass)
        if not name_pass:
    	    return False

	addr_pass = self.addr_filter is None or \
	    remote.address.startswith(self.addr_filter)
	logger.debug("addr_pass: %s" % addr_pass)
        if not addr_pass:
	    return False
	
	class_pass = self.devclass_filter is None or \
            (remote.devclass & self.devclass_filter)>0
            
        logger.debug("class_pass: %s" % class_pass)
        if not class_pass:
	    return False

	rssi_test = record is None or not hasattr(record, 'getAverageRSSI')
	logger.debug("rssi_test: %s" % rssi_test)
	
	if rssi_test:
	    rssi = record.getAverageRSSI()
	    rssi_pass = \
		(self.rssi_min is None or rssi > self.rssi_min ) \
		    or \
                (self.rssi_max is None or rssi < self.rssi_max )
            logger.info("rssi_pass %s, average: %s, min: %s, max: %s" %
        	    (rssi_pass, rssi, self.rssi_min, self.rssi_max)
	    )
	    if not rssi_pass:
		return False

	logger.info("passed all tests")
	return True

def campaign_file_upload_to(instance, filename):
  return os.path.join('campaign',time.strftime("%Y_%m_%d__%H_%M_%S"),filename)

class CampaignFile(models.Model):
    chance = models.DecimalField(
            null=True, 
            blank=True, 
            default=1.0, 
            decimal_places=2, 
            max_digits=3,
            help_text=_("if < 1 then a random number generator will check if "
                "the user is lucky enough to get this file")
    )
    file = models.FileField(
            upload_to=campaign_file_upload_to,
            help_text=_("campaign file itself")
    )
    
    campaign = models.ForeignKey(MarketingCampaign)
    
    def __unicode__(self):
        return "%s: %.2f" % (self.file, self.chance)

class RemoteDevice(models.Model):
    address = models.CharField(
            max_length=17, 
            blank=False,
            verbose_name=_("bluetooth address")
    )
    name = models.CharField(
            max_length=100, 
            blank=True, 
            null=True,
            verbose_name=_("identifying name")
    )
    last_seen = models.DateTimeField(
            auto_now=True, 
            blank=False,
            verbose_name=_("time")
    )
    devclass = models.IntegerField(null=True)
    
    def __unicode__(self):
        return "%s, %s" % (self.address, self.name)

    @classmethod
    def getRemoteDevice(cls, address, name=None, devclass=None):
        qs = cls.objects.filter(address=address)
        if qs.count() == 0:
            logger.info("first time found, not yet known in our DB") 
            remote = RemoteDevice()
            remote.address = address
            remote.name = name
            remote.devclass = devclass
            remote.save()
            return remote
        if qs.count() > 1:
            for i in qs[:1]:
                i.delete()
        return qs[0]

class DeviceRecord(models.Model):
    time = models.DateTimeField(
            blank=False, 
            serialize = True,
            verbose_name=_("time")
    )
    dongle = models.ForeignKey(BluetoothDongle, 
            blank=True, 
            null=True, 
            serialize = True,
            verbose_name=_("dongle address")
    )

    def __unicode__(self):
        return self.dongle.address
    
    def nodeRepresentation(self):
        return "%s - %s [%s]" % (
                                    str(self.time), 
                                    self.dongle.address, 
                                    self._meta.module_name
        )

    class Meta:
        ordering = ['time']

    def save(self, force_insert=False, force_update=False):
        if self.time is None:
            self.time = datetime.utcnow()
        super(DeviceRecord, self).save(force_insert, force_update)


class RemoteBluetoothDeviceRecord(DeviceRecord):
    remote = models.ForeignKey(
            RemoteDevice, 
            verbose_name=_("remote address"), 
            serialize = True
    )

    def setRemoteDevice(self, address):
        self.remote = RemoteDevice.getRemoteDevice(address)

    def __unicode__(self):
        return "%s, %s" % (
            self.dongle.address, 
            self.remote.address
        )

    def nodeRepresentation(self):
        return "%s - %s->%s [%s]" % (
                    str(self.time), 
                    self.dongle.address, 
                    self.remote.address, 
                    self._meta.module_name
    )

    class Meta:
        ordering = ['time']

class RemoteBluetoothDeviceFoundRecord(RemoteBluetoothDeviceRecord):
    __rssi = models.CommaSeparatedIntegerField(
            max_length=200, 
            verbose_name=_("rssi"), 
            serialize = True
    )

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
                                self.__rssi
        )

class RemoteBluetoothDeviceSDP(RemoteBluetoothDeviceRecord):
    channel = models.IntegerField(
        help_text=_("bluetooth rfcomm channel that provides the used service"))
    
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
        ordering = ['time']
    
class RemoteBluetoothDeviceFilesRejected(RemoteBluetoothDeviceFileTry):
    ret_value = models.IntegerField()
    
    def isTimeout(self):
        return self.ret_value is not None and self.ret_value in TIMEOUT_RET
    
    def __unicode__(self):
        return "%s %s, timeout:%s" % (
                        RemoteBluetoothDeviceFileTry.__unicode__(self), 
                        self.ret_value, self.isTimeout()
        )

class RemoteBluetoothDeviceFilesSuccess(RemoteBluetoothDeviceFileTry):

    def save(self, *args, **kwargs):
        super(RemoteBluetoothDeviceFilesSuccess, self).save(*args, **kwargs)

        if self.campaign.accepted_count > -1:
            c = self.campaign.getAcceptedCount()
            logger.info("accepted filter: %s, count: %s" % 
                ( self.campaign.accepted_count, c ) )
            if c >= self.campaign.accepted_count:
                self.campaign.enabled = False
                self.campaign.no_restart = True
                self.campaign.save()

def getMatchingCampaigns(
        remote=None, 
        time_=None,
        enabled=None, 
        classes=None, 
        record=None):
    out  = list()
    classes = classes or Campaign.__subclasses__()
    time_ = time_ or datetime(*time.gmtime()[:-2])
    logger.info("getMatchingCampaigns %s %s %s %s %s" % 
                        ( remote, 
                            time_, 
                            enabled, 
                            classes,
                            record ) )

    for model in classes:
        rules = model.objects

        if enabled is not None:
            rules = rules.filter(enabled=enabled)

        rules = rules.all()
        rules = rules.filter(start__isnull=True) | rules.filter(start__lte=time_)
        rules = rules.filter(end__isnull=True) | rules.filter(end__gte=time_)

        if remote is None:
            out.extend(rules)
            continue

        for rule in rules:
            if rule.matches(remote, record):
                out.append(rule)

    if len(out):
        logger.info("There's a match")
        logger.debug(out)
    return out

def get_campaign_rule(files):
    logger.info('get_campaign_rule %s' % files)
    out = set()

    for file, camp_id in files:
        logger.debug(file)
        try:
            camp = MarketingCampaign.objects.get(pk=camp_id)
            logger.debug(camp)
            if len(out) > 0 and camp not in out:
                logger.error("multiple return values")
            out.add(camp)
        except Exception, err:
            logger.exception(err)
    if len(out) == 0:
        logger.info("couldn't find campaing")
        return None

    logger.info("found camp")
    return list(out)[0]

def __restart_server():
    logger.info("restarting server")
    try:
        server = rpyc.connect('localhost', 8010)
        server.root.restart()
    except:
        #could be that we're only running the web server
        pass

def bluetooth_dongle_signal(instance, **kwargs):
    ''' gets called when ever there is a change in dongles '''
    if isinstance(instance, BluetoothDongle):
        logger.info('bluetooth_dongle_signal')
        __restart_server()

def campaign_signal(instance, **kwargs):
    ''' gets called when ever there is a change in marketing campaigns '''
    if (isinstance(instance, CampaignFile) or isinstance(instance, Campaign)) \
        and not hasattr(instance, 'no_restart'):
            logger.info('campaing_signal')
            __restart_server()

def logline_signal(instance, **kwargs):
    ''' gets called when ever there is a new logline'''
    if isinstance(instance, LogLine):
        if LogLine.objects.count()<100:
            return
        logger.info('logline cache clean up')
        logger.debug("logline count: %s" % LogLine.objects.count())
        qs = LogLine.objects.all().order_by('time')
        idm = qs[0].pk
        idM = qs[qs.count()-50].pk
        LogLine.objects.filter(pk__gte=idm, pk__lte=idM).delete()
        logger.debug("logline count: %s" % LogLine.objects.count())

models.signals.post_save.connect(bluetooth_dongle_signal)
models.signals.post_save.connect(campaign_signal)
models.signals.post_save.connect(logline_signal)

