# -*- coding: utf-8 -*-
# REST interface for OpenProximity
# Copyright (C) 2010 Manuel Coli <manuel@polline.net>
# Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r'MarketingCampaign/(.*?)/?$', 
	  views.json_MarketingCampaign_resource),
    url(r'CampaignFile/get/(?P<pk>\d+)/?$', 
	  views.grab_file),
    url(r'CampaignFile/(.*?)/?$', 
	  views.json_CampaignFile_resource),
    url(r'CampaignFileLast/(.*?)/?$', 
	  views.json_CampaignFile_last_resource),
    url(r'RemoteDevice/(.*?)/?$', 
	  views.json_RemoteDevice_resource),
    url(r'DeviceRecord/(.*?)/?$', 
	  views.json_DeviceRecord_resource),
    url(r'RemoteBluetoothDeviceRecord/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceRecord_resource),
    url(r'RemoteBluetoothDeviceFoundRecord/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceFoundRecord_resource),
    url(r'RemoteBluetoothDeviceSDP/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceSDP_resource),
    url(r'RemoteBluetoothDeviceNoSDP/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceNoSDP_resource),
    url(r'RemoteBluetoothDeviceSDPTimeout/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceSDPTimeout_resource),
    url(r'RemoteBluetoothDeviceFilesRejected/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceFilesRejected_resource),
    url(r'RemoteBluetoothDeviceFilesSuccess/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceFilesSuccess_resource),
    url(r'RemoteBluetoothDeviceFileTry/(.*?)/?$', 
	  views.json_RemoteBluetoothDeviceFileTry_resource),
    url(r'.*', views.index)
)
