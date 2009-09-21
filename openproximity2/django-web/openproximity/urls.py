#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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
from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django import forms
from django.contrib.auth.decorators import login_required
import django.contrib.databrowse as databrowse
from django.contrib.databrowse.datastructures import EasyModel
from django.views.generic.simple import direct_to_template

from models import *
import views

class RemoteRecordForm(forms.ModelForm):
    class Meta:
	model = DeviceRecord
    
databrowse_root = databrowse.DatabrowseSite()
databrowse_root.register(BluetoothDongle)
databrowse_root.register(ScannerBluetoothDongle)
databrowse_root.register(RemoteScannerBluetoothDongle)
databrowse_root.register(RemoteDevice)
databrowse_root.register(RemoteBluetoothDeviceFoundRecord)
databrowse_root.register(RemoteBluetoothDeviceFileTry)
databrowse_root.register(RemoteBluetoothDeviceFilesSuccess)
databrowse_root.register(RemoteBluetoothDeviceFilesRejected)
databrowse_root.register(MarketingCampaign)
databrowse_root.register(CampaignFile)

info_dict = {
    'form_class': RemoteRecordForm,
    'post_save_redirect': '../accepted/',
}

from microblog.sites import TweetSite
def convert(time_string):
    return datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')

blog = TweetSite(LogLine, 'time', convert)

urlpatterns = patterns('',
    (r'^accepted/$', views.add_record_accepted),
    (r'^genericadd/$', 'django.views.generic.create_update.create_object', info_dict),
    (r'^remoteadd/$', views.add_record),
    (r'^data/(.*)$', databrowse_root.root ),
    (r'^rpc/(?P<command>.+)', views.rpc_command),
    (r'^configure/dongle/(?P<address>.+)', views.configure_dongle),
    (r'^configure/dongle/', views.configure_dongle),
    (r'^configure/camp/(?P<camp_name>.+)', views.configure_campaign),
    (r'^configure/camp/', views.configure_campaign),
    (r'^stats/restart.*', views.stats_restart),
    (r'^file/grab/(?P<file>.+)', views.grab_file),
    (r'^microblog/', include(blog.urlpatterns)),
    (r'.*', views.index),
)
