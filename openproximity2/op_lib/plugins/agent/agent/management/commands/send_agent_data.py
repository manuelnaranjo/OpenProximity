#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.db import connection, transaction
from django.utils import translation, simplejson as json
from openproximity.models import RemoteDevice, BluetoothDongle, DeviceRecord, MarketingCampaign
from openproximity.models import RemoteBluetoothDeviceFoundRecord, RemoteBluetoothDeviceSDP, RemoteBluetoothDeviceNoSDP, RemoteBluetoothDeviceSDPTimeout, RemoteBluetoothDeviceFileTry, RemoteBluetoothDeviceFilesRejected, RemoteBluetoothDeviceFilesSuccess
from plugins.agent.agent.models import AgentRecord, AgentDeviceRecord
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
    print time.time(), "generating data"
    content = dict()
    if len(SITEID) > 0:
	content['site-id'] = SITEID
    if len(CUSTID) > 0:
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

def do_post(SERVER, content):
    data,head = multipart_encode({'content': content})
    req = urllib2.Request("%s/push-to-registry/" % SERVER,data, head)
    fd = urllib2.urlopen(req, data)
    return fd.read()

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

@transaction.commit_manually
def do_data_upload(*args, **kwargs):
    for x in args:
	if '=' in x:
	    k, v = x.split('=', 1)
	    kwargs[k] = v
	else:
	    print "ignoring option", x
    
    SERVER=os.environ.get('AGENT_SERVER', None)
    SITEID=os.environ.get('AGENT_SITEID', '')
    CUSTID=os.environ.get('AGENT_CUSTOMERID', '')
    
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
    
    print time.time(), "posting"
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
