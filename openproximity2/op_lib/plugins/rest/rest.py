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

from django.http import HttpResponse
from django_restapi import site
from mimetypes import guess_type as guess_mime
from openproximity.models import *
from django_restapi import authentication, receiver
from django_restapi.model_resource import Collection

def model_register(model, *args, **kwargs):
    '''
      A helper method to reduce the amount of times we write the same.
    '''
    if 'authentication' not in kwargs:
      kwargs['authentication'] = authentication.HttpBasicAuthentication()

    if 'permitted_methods' not in kwargs:
      kwargs['permitted_methods'] = ('GET', 'POST', 'PUT', 'DELETE')

    site.register(model, *args, **kwargs)

class CampaignFileResource(Collection):
    def __init__(self, *args, **kwargs):
	Collection.__init__(self, CampaignFile, *args, **kwargs)
	self.receiver =  receiver.FormReceiver()
	self.permitted_methods = ('GET', 'POST', 'PUT', 'DELETE')

    def getFile(self, request, pk):
	f = CampaignFile.objects.get(pk=pk).file
	mime = guess_mime(f.name)
	return HttpResponse(f.read(), mimetype=mime[0])

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(CampaignFileResource, self).get_urls()
	urls += patterns('',
    		url(r'^get-file/(?P<pk>\d+)/?$', self.getFile, name="get-file"))
        return urls

model_register(MarketingCampaign)
model_register(CampaignFileResource())
model_register(DeviceRecord)
model_register(RemoteDevice)
model_register(RemoteBluetoothDeviceRecord)
model_register(RemoteBluetoothDeviceFoundRecord)
model_register(RemoteBluetoothDeviceSDP)
model_register(RemoteBluetoothDeviceNoSDP)
model_register(RemoteBluetoothDeviceSDPTimeout)
model_register(RemoteBluetoothDeviceFilesRejected)
model_register(RemoteBluetoothDeviceFilesSuccess)
model_register(RemoteBluetoothDeviceFileTry)
