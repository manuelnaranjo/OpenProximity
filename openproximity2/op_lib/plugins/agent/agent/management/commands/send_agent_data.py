#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.db import connection, transaction
from django.utils import translation, simplejson as json
from openproximity.models import RemoteDevice, BluetoothDongle, DeviceRecord, MarketingCampaign, CampaignFile
from openproximity.models import RemoteBluetoothDeviceFoundRecord, RemoteBluetoothDeviceSDP, RemoteBluetoothDeviceNoSDP, RemoteBluetoothDeviceSDPTimeout, RemoteBluetoothDeviceFileTry, RemoteBluetoothDeviceFilesRejected, RemoteBluetoothDeviceFilesSuccess
from plugins.agent.agent.models import AgentRecord, AgentDeviceRecord, AgentMarketingCampaign
from plugins.agent.views import AGENT as SETTINGS
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from itertools import chain

import gzip, httplib, mimetypes, urllib, urllib2, StringIO, os, time

register_openers()

serializer = serializers.get_serializer('json')()
#serializer.options={'indent': 4, 'subclass': True}
serialize=serializer.serialize
deserialize = serializers.get_deserializer('json')

HELP=r"""
  Go through database and upload data to main server.
  
  send_data_agent [options] [agent settings]

Agent Options: (settings=value)
    server=AGENT_SERVER			server to which we connect to
    site_id=AGENT_SITEID		siteID used to identify with the server
    customer_id=AGENT_CUSTOMERID	customerID used to identify with the 
					server
    save_settings=[False]		if present then any change to customer_id or
					agent_id will be persisted to settings file
					
    by default this settings are taken from /etc/openproximity2/settings.xml
    except for save_settings which should be used wisely (only once)
"""

class Command(BaseCommand):
    help = "OpenProximity Agent Uploader."
    args = "[several KEY=val options, use `send_data_agent help` for help]"
    
    def handle(self, *args, **kwargs):

	try:
	    translation.activate(settings.LANGUAGE_CODE)
	except AttributeError:
	    pass
	do_data_upload(*args, **kwargs)
	
    def usage(self, subcommand):
	return HELP

def getRemoteDeviceIterator():
    classes = [ RemoteBluetoothDeviceFoundRecord, 
		RemoteBluetoothDeviceSDP, 
		RemoteBluetoothDeviceNoSDP, 
		RemoteBluetoothDeviceSDPTimeout, 
		RemoteBluetoothDeviceFileTry, 
		RemoteBluetoothDeviceFilesRejected, 
		RemoteBluetoothDeviceFilesSuccess
	]
    a=list()
    for b in classes:
	a.append(b.objects.filter(agentdevicerecord__commited=False).all())
    for clas in a:
	for element in clas:
	    yield element

def compress_data(non_compressed):
    stream = StringIO.StringIO()
    gzipper = gzip.GzipFile(fileobj=stream,mode='wb')
    gzipper.write(non_compressed)#.encode('utf-8'))
    gzipper.close()
    stream.name="content"
    return stream

def generate_data(SITEID, CUSTID):
    print time.time(), "generating data", SITEID, CUSTID
    content = dict()
    if SITEID and len(SITEID) > 0:
	content['site-id'] = SITEID
    if CUSTID and len(CUSTID) > 0:
	content['customer-id'] = CUSTID

    print time.time(), "remote-devices"
    content['remote-devices'] = serialize(
        RemoteDevice.objects.filter(remotebluetoothdevicerecord__agentdevicerecord__commited=False).distinct(),
    )
    
    print time.time(), "bluetooth-dongles"
    content['bluetooth-dongles'] = serialize(
	BluetoothDongle.objects.filter(devicerecord__agentdevicerecord__commited=False).distinct(),
	subclass=True,
    )
    
    print time.time(), "campaigns-marketing"
    content['campaigns-marketing'] = serialize(
        MarketingCampaign.objects.filter(remotebluetoothdevicefiletry__agentdevicerecord__commited=False).distinct(),
        subclass=True
    )


    print time.time(), "agent-records"
    content['agent-records'] = serialize(
        AgentRecord.objects.filter(commited=False).all(),
        excludes=('commited'),
    )

    print time.time(), "device-records"
    content['device-records'] = serialize(
        getRemoteDeviceIterator(),
        #subclass=True,
    )
    return content

def do_post(SERVER, content, function='push-to-registry'):
    data,head = multipart_encode({'content': content})
    req = urllib2.Request("%s/%s/" % (SERVER, function),data, head)
    fd = urllib2.urlopen(req, data)
    return fd.read()

def grab_file(SERVER, file_name):
    url = "%s/get-files/%s" % (SERVER, file_name)
    print time.time(), "grabbing %s" % url
    req = urllib2.Request(url)
    file_name = os.path.join(settings.MEDIA_ROOT, file_name)
    fd = urllib2.urlopen(req)
    try:
	os.makedirs(os.path.dirname(file_name))
    except:
	# folder might all ready exist
	pass
    a = file(file_name, 'w')
    a.write(fd.read())
    a.close()
    print time.time(), "saved", file_name

def slice(records, size=100):
    i = 0
    while i < len(records):
	yield records[i:i+size]
	i+=size

def reply_process_agent_records(records):
    print time.time(), "updating agent-records, %s records" % len(records)
    for sub in slice(records):
	AgentRecord.objects.filter(id__in=sub).update(commited=True)
    return True

def reply_process_device_records(records):
    print time.time(), "updating device-records, %s records" % len(records)
    for sub in slice(records):
	AgentDeviceRecord.objects.filter(record__id__in=sub).update(commited=True)
    return True
    
def do_campaing_sync(data, SERVER):
    camps = dict()
    
    for camp in json.loads(data['camps']):
	# create campaign objects from server request
	if camp['model'] != 'op_www.sitemarketingcampaign':
	    print "model not supported yet", camp['model']
	    continue
	ncamp = AgentMarketingCampaign()
	fields = camp['fields']
	for field, val in fields.iteritems():
	    print field
	    setattr(ncamp, field, val)
	ncamp.save()
	camps[camp['pk']]=ncamp
    
    for file in json.loads(data['files']):
	if file['model'] != "openproximity.campaignfile":
	    print "file type not supported yet", file['model']
	# create file objects from server request
	nfile = CampaignFile()
	fields = file['fields']
	for field, val in fields.iteritems():
	    if field not in ['campaign',]:
		print field
		setattr(nfile, field, val)
	nfile.campaign = camps[fields['campaign']]
	nfile.save()

	#grab file it self
	grab_file(SERVER, fields['file'])
    
    # don't commit changes until we got the full campaign
    transaction.commit()



@transaction.commit_manually
def do_data_upload(*args, **kwargs):
    for x in args:
	if '=' in x:
	    k, v = x.split('=', 1)
	    kwargs[k] = v
	else:
	    print "ignoring option", x
    
    SERVER=SETTINGS.get('server', "http://www.openproximity.com/stats")
    SITEID=SETTINGS.get('site', "")
    CUSTID=SETTINGS.get('customer', "")
    
    if kwargs.get('server', None):
	SERVER=kwargs.get('server')
    
    if kwargs.get('site_id', None):
	SITEID=kwargs.get('site_id')
    
    if kwargs.get('customer_id', None):
	CUSTID=kwargs.get('customer_id')

    post_data = generate_data(SITEID, CUSTID)
    
    if kwargs.get('debug', None):
	for key, val in post_data.items():
	    if key in ['site-id','customer-id']:
		print val
	    else:
		print json.loads(val)
	return
    
    print time.time(), "dumping"
    post_data = json.dumps(post_data)
    print time.time(), "data-generated"
    
    compress = compress_data(post_data)

    print time.time(), 'uncompressed', len(post_data)
    
    print time.time(), "posting to", SERVER
    reply = do_post(SERVER, compress)
    print time.time(), "got-reply"

    reply = json.loads(reply)
    print time.time(), "got json"

    reply_process_agent_records(reply.get('agent-records',list()))
    transaction.commit()
    
    reply_process_device_records(reply.get('device-records',list()))
    transaction.commit()
    
    print reply['customer-id'], reply['site-id']
    
    if 'error' in reply:
	raise Exception(reply['error'])
	
    if 'available-campaigns' in reply:
	new_camps = list()
	for camp in reply['available-campaigns']:
	    if AgentMarketingCampaign.objects.filter(
		    hash_id=camp['hash_id'],
		    last_modification=camp['last_modification']).count() == 0:
		new_camps.append(hash_)
    
	print "new camps available, I need to get %s camps" % len(new_camps)
    
	print time.time(), "dumping"
	post_data = json.dumps({'campaigns': new_camps})
	print time.time(), "data-generated"
    
	compress = compress_data(post_data)

	print time.time(), 'uncompressed', len(post_data)
    
	print time.time(), "posting to", SERVER
	camps = json.loads(do_post(SERVER, compress, 'get-campaigns'))
	print time.time(), "got-reply"
	print camps
	do_campaing_sync(camps, SERVER)
	transaction.commit()

	
    if kwargs.get('save_settings', 'false').lower()=='true':
	SETTINGS['customer']=reply['customer-id']
	SETTINGS['site']=reply['site-id']
	op = settings.OPENPROXIMITY.getDict('/')
	op['agent'] = SETTINGS
	settings.OPENPROXIMITY.saveSettings(op)
