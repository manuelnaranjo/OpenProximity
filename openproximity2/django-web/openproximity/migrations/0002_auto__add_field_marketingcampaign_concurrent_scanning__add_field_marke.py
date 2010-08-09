# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'MarketingCampaign.concurrent_scanning'
        db.add_column('openproximity_marketingcampaign', 'concurrent_scanning', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'MarketingCampaign.upload_on_discovered'
        db.add_column('openproximity_marketingcampaign', 'upload_on_discovered', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'MarketingCampaign.concurrent_scanning'
        db.delete_column('openproximity_marketingcampaign', 'concurrent_scanning')

        # Deleting field 'MarketingCampaign.upload_on_discovered'
        db.delete_column('openproximity_marketingcampaign', 'upload_on_discovered')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'openproximity.bluetoothdongle': {
            'Meta': {'object_name': 'BluetoothDongle'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '17'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'openproximity.campaignfile': {
            'Meta': {'object_name': 'CampaignFile'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['openproximity.MarketingCampaign']"}),
            'chance': ('django.db.models.fields.DecimalField', [], {'default': '1.0', 'null': 'True', 'max_digits': '3', 'decimal_places': '2', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'openproximity.devicerecord': {
            'Meta': {'object_name': 'DeviceRecord'},
            'dongle': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['openproximity.BluetoothDongle']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'openproximity.logline': {
            'Meta': {'object_name': 'LogLine'},
            'content': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'openproximity.marketingcampaign': {
            'Meta': {'object_name': 'MarketingCampaign'},
            'accepted_count': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'addr_filter': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'concurrent_scanning': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'devclass_filter': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'dongle_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fixed_channel': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_filter': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'pin_code': ('django.db.models.fields.CharField', [], {'default': "'1234'", 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'rejected_count': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'rejected_timeout': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'rssi_max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rssi_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'service': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tries_count': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'tries_timeout': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'upload_on_discovered': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'openproximity.remotebluetoothdevicefilesrejected': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceFilesRejected', '_ormbases': ['openproximity.RemoteBluetoothDeviceFileTry']},
            'remotebluetoothdevicefiletry_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceFileTry']", 'unique': 'True', 'primary_key': 'True'}),
            'ret_value': ('django.db.models.fields.IntegerField', [], {})
        },
        'openproximity.remotebluetoothdevicefilessuccess': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceFilesSuccess', '_ormbases': ['openproximity.RemoteBluetoothDeviceFileTry']},
            'remotebluetoothdevicefiletry_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceFileTry']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.remotebluetoothdevicefiletry': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceFileTry', '_ormbases': ['openproximity.RemoteBluetoothDeviceRecord']},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['openproximity.MarketingCampaign']"}),
            'remotebluetoothdevicerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceRecord']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.remotebluetoothdevicefoundrecord': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceFoundRecord', '_ormbases': ['openproximity.RemoteBluetoothDeviceRecord']},
            '_RemoteBluetoothDeviceFoundRecord__rssi': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '200'}),
            'remotebluetoothdevicerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceRecord']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.remotebluetoothdevicenosdp': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceNoSDP', '_ormbases': ['openproximity.RemoteBluetoothDeviceRecord']},
            'remotebluetoothdevicerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceRecord']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.remotebluetoothdevicerecord': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceRecord', '_ormbases': ['openproximity.DeviceRecord']},
            'devicerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.DeviceRecord']", 'unique': 'True', 'primary_key': 'True'}),
            'remote': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['openproximity.RemoteDevice']"})
        },
        'openproximity.remotebluetoothdevicesdp': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceSDP', '_ormbases': ['openproximity.RemoteBluetoothDeviceRecord']},
            'channel': ('django.db.models.fields.IntegerField', [], {}),
            'remotebluetoothdevicerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceRecord']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.remotebluetoothdevicesdptimeout': {
            'Meta': {'object_name': 'RemoteBluetoothDeviceSDPTimeout', '_ormbases': ['openproximity.RemoteBluetoothDeviceRecord']},
            'remotebluetoothdevicerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.RemoteBluetoothDeviceRecord']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.remotedevice': {
            'Meta': {'object_name': 'RemoteDevice'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '17'}),
            'devclass': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'openproximity.remotescannerbluetoothdongle': {
            'Meta': {'object_name': 'RemoteScannerBluetoothDongle', '_ormbases': ['openproximity.ScannerBluetoothDongle']},
            'local_dongle': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'remote_dongles'", 'to': "orm['openproximity.ScannerBluetoothDongle']"}),
            'scannerbluetoothdongle_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.ScannerBluetoothDongle']", 'unique': 'True', 'primary_key': 'True'})
        },
        'openproximity.scannerbluetoothdongle': {
            'Meta': {'object_name': 'ScannerBluetoothDongle', '_ormbases': ['openproximity.BluetoothDongle']},
            'bluetoothdongle_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.BluetoothDongle']", 'unique': 'True', 'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {})
        },
        'openproximity.setting': {
            'Meta': {'object_name': 'Setting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'value': ('net.aircable.fields.PickledField', [], {'max_length': '200'})
        },
        'openproximity.uploaderbluetoothdongle': {
            'Meta': {'object_name': 'UploaderBluetoothDongle', '_ormbases': ['openproximity.BluetoothDongle']},
            'bluetoothdongle_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['openproximity.BluetoothDongle']", 'unique': 'True', 'primary_key': 'True'}),
            'max_conn': ('django.db.models.fields.IntegerField', [], {'default': '7'})
        },
        'openproximity.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timezone': ('timezones.fields.TimeZoneField', [], {'default': "'America/Argentina/Buenos_Aires'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['openproximity']
