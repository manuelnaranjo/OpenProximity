from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
import signals.scanner as scanner
import time
from datetime import datetime

TIMEOUT_RET = [ 22 ]

class BluetoothDongle(models.Model):
    address = models.CharField(max_length=17, 
	blank=False,
	verbose_name=_("bluetooth address"))
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
	return "Scanner: %s, %s" % (BluetoothDongle.__unicode__(self), self.priority)

class UploaderBluetoothDongle(BluetoothDongle):
    max_conn = models.IntegerField(default=7,
	verbose_name=_("connections"),
	help_text=_("maximum allowed connections"))
	
    def __unicode__(self):
	return "Uploader: %s, %s" % (BluetoothDongle.__unicode__(self), self.max_conn)

SERVICE_TYPES = (
    (0,	  u'opp'),
    (1,	  u'ftp'),
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
	
	if self.files.count() > 0:
	    out+="files: "
	    for file in self.files.all():
		out+="%s, " % file.__unicode__()
	return out.strip()[:-1]

CampaignFile.rules = models.ManyToManyField(CampaignRule)

class MarketingCampaign(models.Model):
    friendly_name = models.CharField(max_length=100)
    rules = models.ForeignKey(CampaignRule)
    
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
	return "%s, %s, %s, %s" % (self.address, self.name, self.devclass, self.last_seen)

class DeviceRecord(models.Model):
    time = models.DateTimeField(auto_now=True, blank=False,
	verbose_name=_("time"))
    dongle = models.ForeignKey(BluetoothDongle, blank=True, null=True,
	verbose_name=_("dongle address"))

    def __unicode__(self):
	return "%s, %s" % (self.dongle.address, self.time)#, self.action)	

class RemoteBluetoothDeviceRecord(DeviceRecord):
    remote = models.ForeignKey(RemoteDevice, verbose_name=_("remote address"))

    def setRemoteDevice(self, address):
	try:
	    self.remote=RemoteDevice.objects.get(address=address)
	except Exception, err:
	    print err
    
    def __unicode__(self):
	return "%s, %s, %s" % (
	    self.dongle.address, 
	    self.remote.address,
	    self.time
	)
	
class RemoteBluetoothDeviceFoundRecord(RemoteBluetoothDeviceRecord):
    rssi = models.IntegerField(verbose_name=_("average rssi"))
    amount_results = models.IntegerField(
	help_text=_("amount of times we discovered this device on a scan cycle"))
#    action = 130
#    campaign = models.ForeignKey(CampaignRule)
    					
    def __unicode__(self):
	return "%s, %s, %s, %i" % (
	    self.dongle.address, 
	    self.remote.address,
	    self.time,
	    self.rssi)

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
    rule = models.ForeignKey(CampaignRule)
    
class RemoteBluetoothDeviceFilesRejected(RemoteBluetoothDeviceFileTry):
    ret_value = models.IntegerField()
    
    def isTimeout(self):
	return self.ret_value is not None and self.ret_value in TIMEOUT_RET
	
    def __unicode__(self):
	return "%s %s" % (RemoteBluetoothDeviceFileTry.__unicode__(self), self.ret_value)

class RemoteBluetoothDeviceFilesSuccess(RemoteBluetoothDeviceFileTry):
    pass

def getMatchingCampaigns(remote=None, time_=datetime.fromtimestamp(time.time())):
    print "getMatchingCampaigns", time_
    out  = list()
    rules = CampaignRule.objects.all()
    
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
