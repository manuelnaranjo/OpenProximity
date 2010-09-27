#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib2, json, pprint, rest

klass = 'openproximity/marketingcampaign'

usage='''
Usage:
    %s <url> <command>
    
Commands:
    list	: list all campaigns
    get	 <id>	: get campaign <id>
    update <id> datafile: update a campaign with the given python dict
    delete <id> : delete campaign <id>
    test:	run tests
'''

def list(url):
    return json.loads(rest.list(url, klass ))

def get(url, pk, *args, **kwargs):
    return json.loads(rest.get(url, klass, pk))

def post(url, data, *args, **kwargs):
    data=json.dumps(eval(file(data).read()))
    data, url = rest.post(url, klass, data)
    return json.loads(data), url

def put(url, pk, data, *args, **kwargs):
    data=json.dumps(eval(file(data).read()))
    data, url = rest.put(url, klass, pk, data)
    return json.loads(data), url

def delete(url, pk, *args, **kwargs):
    return rest.delete(url, klass, pk)

def test(url):
    print "registered campaigns"
    pp=pprint.PrettyPrinter(indent=4)
    pp.pprint(list(url))

    data = [{
	u'fields': {
	  u'accepted_count': -1,
	  u'addr_filter': None,
	  u'concurrent_scanning': False,
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
	  u'tries_timeout': 0,
	  u'upload_on_discovered': False
	},
	u'model': u'openproximity.marketingcampaign',
	u'pk': 1
    }]
    
    print "creating campaign"
    data=json.dumps(data)
    data = json.loads(rest.post(url, klass, data))
    pp.pprint(data)
    print "created"
    
    print "editing campaign"
    data[0][u'fields'][u'name']=u'Test 2'
    pk=data[0]['pk']
    data=json.dumps(data)
    data = rest.put(url, klass, pk, data)
    data=json.loads(data)
    pp.pprint(data)

    print "deleting campaign"
    pp.pprint(delete(url, pk))


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

