#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib2, json, pprint, rest
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

klass = 'CampaignFile'

usage='''
Usage:
    %s <url> <command>
    
Commands:
    list	: list all campaigns
    get	 <id>	: get binary file <id>
    post <campaign> <chance> <filename>: posts a file to the server
    delete <id> : delete campaign <id>
    test	: run a battery of tests
'''

def list(url):
    return json.loads(rest.list(url, klass ))

def get(url, pk, out, *args, **kwargs):
    A=urllib2.urlopen("%s/REST/%s/get/%s/" % (url, klass,pk)).read()
    B=file(out, 'wb')
    B.write(A)
    B.close()
    return "Got file, %s bytes" % len(A)

def post(url, campaign, chance, data, *args, **kwargs):
    b=( 
	('file', open(data, 'rb')),
	('campaign', campaign),
	('chance', chance),
    )

    datagen, headers = multipart_encode(b)

    return json.loads(
	rest.post(
	    url=url, 
	    klass=klass, 
	    data=''.join(datagen),
	    headers=headers
	)
   )

def put(url, pk, campaign, chance, data, *args, **kwargs):
    b=( 
	('file', open(data, 'rb')),
	('campaign', campaign),
	('chance', chance),
    )

    datagen, headers = multipart_encode(b)

    return json.loads(
	rest.put(
	    url=url, 
	    klass=klass, 
	    pk=pk,
	    data=''.join(datagen),
	    headers=headers
	)
   )

def delete(url, pk, *args, **kwargs):
    return rest.delete(url, klass, pk)

def test(url):
    def create_campaign(url):
      data = [{
	u'fields': {
	  u'accepted_count': -1,
	  u'addr_filter': None,
	  u'devclass_filter': None,
	  u'dongle_name': u'Test Dongle',
	  u'enabled': True,
	  u'end': None,
	  u'fixed_channel': None,
	  u'name': u'Test Campaign',
	  u'name_filter': u'Test Name',
	  u'pin_code': u'test',
	  u'rejected_count': 2,
	  u'rejected_timeout': -1,
	  u'rssi_max': None,
	  u'rssi_min': None,
	  u'service': 0,
	  u'start': None,
	  u'tries_count': -1,
	  u'tries_timeout': 0
	},
	u'model': u'openproximity.marketingcampaign',
	u'pk': 1
      }]
      print "creating test campaign"
      data=json.dumps(data)
      data=json.loads(rest.post(url, 'MarketingCampaign', data))
      print "created"
      return data[0]['pk']

    def delete_campaign(url, pk):
      rest.delete(url, 'MarketingCampaign', pk)

    print "registered campaign files"
    pp=pprint.PrettyPrinter(indent=4)
    pp.pprint(list(url))

    print "creating marketing file"
    import tempfile, os
    camp_pk=create_campaign(url)
    name = tempfile.mktemp()
    print name
    o = file(name, 'wb')
    o.write("test file")
    o.close()
    d = post(url, camp_pk, 1.0, name)
    file_pk = d[0]['pk']
    pp.pprint(d)
    
    print "getting file"
    get(url, file_pk, name)
    pp.pprint(file(name, 'rb').read())
    
    print "updating campaign"
    d = put(url, file_pk, camp_pk, 0.5, name)
    pp.pprint(d)
    
    print "deleting campaign file"
    delete(url, file_pk)
    delete_campaign(url, camp_pk)
    os.remove(name)

if __name__=='__main__':
    if len(sys.argv) < 2:
	print usage % sys.argv[0]
	sys.exit(1)

    url = sys.argv[1]
    command = sys.argv[2]

    rest.login(url)

    if command == 'list':
	a = list(url)
    elif command=='get':
	a = get(url, *sys.argv[3:])
    elif command=='post':
	a = post(url, *sys.argv[3:])
    elif command=='put':
	a = put(url, *sys.argv[3:])
    elif command=='delete':
	a = delete(url, *sys.argv[3:])
    elif command=='test':
	test(url)
	sys.exit(0)
    else:
	raise Exception("Invalid command")
    
    pp=pprint.PrettyPrinter(indent=4)
    pp.pprint(a)

    sys.exit(0)

