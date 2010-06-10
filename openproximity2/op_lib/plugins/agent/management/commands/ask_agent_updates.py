#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.db import connection, transaction
from django.utils import translation, simplejson as json
from openproximity.models import RemoteDevice, BluetoothDongle, DeviceRecord, MarketingCampaign, CampaignFile
from openproximity.models import RemoteBluetoothDeviceFoundRecord, RemoteBluetoothDeviceSDP, RemoteBluetoothDeviceNoSDP, RemoteBluetoothDeviceSDPTimeout, RemoteBluetoothDeviceFileTry, RemoteBluetoothDeviceFilesRejected, RemoteBluetoothDeviceFilesSuccess

try:
	from plugins.agent.models import AgentRecord, AgentDeviceRecord, AgentMarketingCampaign
	from plugins.agent.views import AGENT as SETTINGS
except:
	from agent.models import AgentRecord, AgentDeviceRecord, AgentMarketingCampaign
	from agent.views import AGENT as SETTINGS
	
from subprocess import Popen, PIPE
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
  Connect to server and ask if there are commands I should run.
  
  send_data_agent [options] [agent settings]

Agent Options: (settings=value)
	server=AGENT_SERVER			server to which we connect to
	site_id=AGENT_SITEID		siteID used to identify with the server
	customer_id=AGENT_CUSTOMERID	customerID used to identify with the 
					server
	dry_run=[True]			don't really execute command
	
	by default this settings are taken from /etc/openproximity2/settings.xml
	except for save_settings which should be used wisely (only once)
"""

class Command(BaseCommand):
	help = "OpenProximity Agent Command Runner."
	args = "[several KEY=val options, use `send_data_agent help` for help]"
	
	def handle(self, *args, **kwargs):

		try:
			translation.activate(settings.LANGUAGE_CODE)
		except AttributeError:
			pass
		do_work(*args, **kwargs)
	
	def usage(self, subcommand):
		return HELP

def do_post(SERVER, content, function='push-to-registry'):
	req = urllib2.Request("%s/%s/" % (SERVER, function),)
	fd = urllib2.urlopen(req, urllib.urlencode(content))
	return fd.read()

def do_commands(commands, dry_run):
	out = dict()
	for pk, command in commands.iteritems():
		stdout = ""
		stderr = ""
		retval = 0
		out[pk]=list()
		for line in command.splitlines():
			if line.strip() == 0:
				continue
			print time.time(), "executing", line
			p = Popen(line.split(), 
#				shell=True, 
				stdout=PIPE, 
				stderr=PIPE)
			stdout+="%s\n" % p.stdout.read()
			stderr+="%s\n" % p.stderr.read()
			if p.returncode:
				retval+=p.returncode
		out[pk]={'stdout': stdout, 'stderr': stderr, 'retval': retval}
	return out

@transaction.commit_manually
def do_work(*args, **kwargs):
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

	post_data = {'site-id': SITEID, 'customer-id': CUSTID}
		
	print time.time(), "posting to", SERVER
	reply = do_post(SERVER, post_data, 'remote-commands-get')
	print time.time(), "got-reply"

	reply = json.loads(reply)
	print time.time(), "got json"
	print time.time(), reply
	
	dry_run = kwargs.get('dry_run', 'false').lower()=='false'
	
	if 'commands' in reply:
		output = do_commands(reply['commands'], dry_run)
	
	do_post(SERVER, {'result': json.dumps(output)}, 'remote-commands-result')
