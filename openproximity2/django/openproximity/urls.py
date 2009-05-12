from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django import forms
from django.contrib.auth.decorators import login_required
import django.contrib.databrowse as databrowse
from django.contrib.databrowse.datastructures import EasyModel

from models import *
import views

class RemoteRecordForm(forms.ModelForm):
    class Meta:
	model = DeviceRecord
    
databrowse_root = databrowse.DatabrowseSite()
databrowse_root.register(BluetoothDongle)
databrowse_root.register(ScannerBluetoothDongle)
databrowse_root.register(DeviceRecord)
databrowse_root.register(RemoteDevice)
databrowse_root.register(RemoteBluetoothDeviceFoundRecord)

databrowse_root.register(MarketingCampaign)
databrowse_root.register(CampaignRule)
databrowse_root.register(CampaignFile)

info_dict = {
    'form_class': RemoteRecordForm,
    'post_save_redirect': '../accepted/',
}

urlpatterns = patterns('',
    (r'^accepted/$', views.add_record_accepted),
    (r'^genericadd/$', 'django.views.generic.create_update.create_object', info_dict),
    (r'^remoteadd/$', views.add_record),
    (r'^(.*)$', login_required(databrowse_root.root) ),
)
