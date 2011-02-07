"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
import methods
import models
import time
from random import randrange
from os import environ
from openproximity import models as op_models
import urllib, httplib
from dojo_util import json_encode, json_decode

class SettingsTest(TestCase):
    def test_000_valid_keys_default_value(self):
	self.assertEqual(methods.getSetting('server'), None)
	self.assertEqual(methods.getSetting('hash_id'), None)
	self.assertEqual(methods.getSetting('password'), None)
	self.assertEqual(methods.getSetting('enabled'), False)
	self.assertEqual(methods.getSetting('enabled', True), True)
	self.assertEqual(methods.getSetting('enabled', 'True'), True)

	for k in ['minute', 'hour', 'dom', 'month', 'dow']:
	    self.assertEqual(methods.getSetting('cron_%s' % k), None)
	    self.assertEqual(methods.getSetting('cron_%s' % k, '*/15'), '*/15')
	    self.assertEqual(methods.getSetting('cron_%s' % k, '*'), '*')

	self.assertEqual(methods.getSetting('server', 'http://test.com'), 
							'http://test.com')

    def test_001_invalid_keys(self):
	self.assertRaises(Exception, methods.getSetting('hash_id'))
	self.assertRaises(ValueError, methods.getSetting, 'enabled', 
								'Some Crap')

    def test_002_set_settings(self):
	self.assertEqual(methods.setSetting('enabled', True), True)
	self.assertEqual(methods.setSetting('server', 'http://test.com'),
						    'http://test.com')

    def __init_op__(self):
	dongle = op_models.ScannerBluetoothDongle.objects.get_or_create(
	    address="00:25:BF:00:00:00",
	    defaults={
		'name': 'Test Scanner',
		'priority': 1,
		'enabled': True
	    })[0]
	dongle.save()
	remote = op_models.RemoteDevice.objects.get_or_create(
	    address="00:25:BF:00:00:00",
	    defaults={
		'name': 'Test Device',
	    })[0]
	remote.save()
	camp = op_models.MarketingCampaign(service=0)
	return dongle, remote


    def __generate_found_records(self, amount_records):
	dongle, remote=self.__init_op__()

	start = time.time()
	for i in range(amount_records):
	    rec = op_models.RemoteBluetoothDeviceFoundRecord(dongle=dongle, 
		remote=remote, 
		time=time.strftime('%Y-%m-%d %H:%M', time.gmtime(start)))
	    rec.setRSSI([randrange(-120, -10) for x in range(randrange(0, 20))])
	    rec.save()
	    start+=randrange(1, 10)

    def __generate_sdp_records(self, amount_records):
	dongle, remote=self.__init_op__()

	start = time.time()
	for i in range(amount_records):
	    rec = op_models.RemoteBluetoothDeviceSDP(dongle=dongle, 
		remote=remote, 
		time=time.strftime('%Y-%m-%d %H:%M', time.gmtime(start)),
		channel=randrange(1,80))
	    rec.save()
	    start+=randrange(1, 10)

    def test_003_test_found_records(self):
	# make sure we have an empty DB
	pks=methods.getLockOverRecords(models.uploadFoundRecord)
	methods.deleteRecords(models.uploadFoundRecord, pks)

	amount_records=randrange(10,30)
	self.__generate_found_records(amount_records)

	pks=methods.getLockOverRecords(models.uploadFoundRecord)
	self.assertEqual(amount_records, len(pks))
	records = methods.getRecordsForUpload(models.uploadFoundRecord, pks)
	self.assertEqual(amount_records, methods.unlockRecords(models.uploadFoundRecord, pks))
	self.assertEqual(methods.deleteRecords(models.uploadFoundRecord, pks), None)
	self.assertEqual(amount_records, op_models.RemoteBluetoothDeviceFoundRecord.objects.count())
	self.assertEqual(0, len(methods.getRecordsForUpload(models.uploadFoundRecord, pks)))

    def test_004_push_scan_data_into_server(self):
	for key in ['server', 'hash_id', 'password']:
	    self.assertTrue('agent2_%s' % key in environ)
    	    methods.setSetting(key, environ['agent2_%s' % key])

	amount_records=randrange(10,30)
	self.__generate_found_records(amount_records)

	pks=methods.getLockOverRecords(models.uploadFoundRecord)
	records = methods.getRecordsForUpload(models.uploadFoundRecord, pks)
        remotes = methods.getRemotesForUpload(models.uploadFoundRecord, pks)
        
	self.assertEqual(amount_records, 
		methods.pushRecords(models.uploadFoundRecord, records, remotes)
	)

    def test_005_test_sdp_records(self):
	# make sure we have an empty DB
	pks=methods.getLockOverRecords(models.uploadFoundRecord)
	methods.deleteRecords(models.uploadFoundRecord, pks)

	camp1 = op_models.MarketingCampaign(service=0, enabled=False, start=None, end=None)
	camp2 = op_models.MarketingCampaign(service=1, enabled=False, start=None, end=None)
	camp1.save()
	camp2.save()

	amount_records=randrange(10,30)
	self.__generate_sdp_records(amount_records)

	camp1.enabled=True
	camp1.save()
	self.__generate_sdp_records(amount_records)

	camp2.enabled=True
	camp2.save()
	self.__generate_sdp_records(amount_records)

	pks=methods.getLockOverRecords(models.uploadSDPRecord)
	self.assertEqual(amount_records*3, len(pks))
	records = methods.getRecordsForUpload(models.uploadSDPRecord, pks)
	self.assertEqual(amount_records*3, methods.unlockRecords(models.uploadSDPRecord, pks))
	self.assertEqual(methods.deleteRecords(models.uploadSDPRecord, pks), None)
	self.assertEqual(amount_records*3, op_models.RemoteBluetoothDeviceSDP.objects.count())
	self.assertEqual(0, len(methods.getRecordsForUpload(models.uploadSDPRecord, pks)))

	op_models.MarketingCampaign.objects.filter(pk__in=[camp1.pk, camp2.pk]).delete()

    def test_006_push_sdp_data_into_server(self):
	for key in ['server', 'hash_id', 'password']:
	    self.assertTrue('agent2_%s' % key in environ)
    	    methods.setSetting(key, environ['agent2_%s' % key])

	camp1 = op_models.MarketingCampaign(service=0, enabled=False)
	camp2 = op_models.MarketingCampaign(service=1, enabled=False)
	camp1.save()
	camp2.save()

	amount_records=randrange(10,30)
	self.__generate_sdp_records(amount_records)

	camp1.enabled=True
	camp1.save()
	self.__generate_sdp_records(amount_records)

	camp2.enabled=True
	camp2.save()
	self.__generate_sdp_records(amount_records)


	pks=methods.getLockOverRecords(models.uploadSDPRecord)
	records = methods.getRecordsForUpload(models.uploadSDPRecord, pks)
        remotes = methods.getRemotesForUpload(models.uploadSDPRecord, pks)

	self.assertEqual(amount_records*3, 
	    methods.pushRecords(models.uploadSDPRecord, records, remotes))
	op_models.MarketingCampaign.objects.filter(pk__in=[camp1.pk, camp2.pk]).delete()

    def test_007_test_helper(self):
	for key in ['server', 'hash_id', 'password']:
	    self.assertTrue('agent2_%s' % key in environ)
    	    methods.setSetting(key, environ['agent2_%s' % key])

	amount_records=randrange(10,30)
	self.__generate_found_records(randrange(10,30))
	camp1=op_models.MarketingCampaign(service=randrange(0,1), enabled=True)
	camp1.save()
	self.__generate_sdp_records(randrange(10,30))
	self.assertTrue(methods.doRecordsAndLog())
	op_models.MarketingCampaign.objects.filter(pk__in=[camp1.pk]).delete()
