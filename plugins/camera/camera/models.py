# -*- coding: utf-8 -*-
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

# agent plugin
# defines new clases for db integration

from openproximity.models import RemoteDevice, RemoteBluetoothDeviceRecord, Campaign, \
	    BluetoothDongle, SERVICE_TYPES, RemoteBluetoothDeviceFoundRecord
from django.db import models
from django.utils.translation import ugettext as _
from datetime import datetime
from django.forms import widgets
from net.aircable.utils import logger
import time

class CameraBluetoothDongle(BluetoothDongle):
    max_conn = models.IntegerField(
	default=4,
	help_text=_("maximum allowed cameras to handle at the same time"),
	verbose_name=_("connections"))

CameraBluetoothDongle._meta.get_field_by_name('enabled')[0].default=True

class CameraRemoteDevice(RemoteDevice):
    latest_served=models.DateTimeField(auto_now=True, editable=False)

class CameraRecord(RemoteBluetoothDeviceRecord):
    picture = models.FileField(upload_to='camera')

class CameraCampaign(Campaign):
    use_backend = models.BooleanField(
	default = False,
	help_text=_("Enable if you want to use OpenProximity as data backend"),
	blank = True)
    enable_zm = models.BooleanField(
	default = False,
	help_text=_("Do you want to enable ZoneMinder link?"),
	blank = True)
    zm_address = models.CharField(
	max_length=100,
	blank = True,
	null = True,
	help_text=_("Address to your ZoneMinder server")
    )

    def matches(self, remote, *args, **kwargs):
	if remote.name and remote.name.lower() in ['optieye']:
	    return True
	return False
