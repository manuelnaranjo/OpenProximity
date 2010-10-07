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
from django_restapi import model_resource
from django_restapi.responder import *
from django_restapi.receiver import *
from django_restapi.authentication import *
from mimetypes import guess_type as guess_mime
from openproximity.models import *

def collection(queryset, *args, **kwargs):
    '''
      A helper method to reduce the amount of times we write the same.
    '''
    if 'authentication' not in kwargs:
      kwargs['authentication'] = HttpBasicAuthentication()

    if 'permitted_methods' not in kwargs:
      kwargs['permitted_methods'] = ('GET', 'POST', 'PUT', 'DELETE')

    if 'receiver' not in kwargs:
      kwargs['receiver'] = JSONReceiver()

    if 'responder' not in kwargs:
      kwargs['responder'] = JSONResponder()

    return model_resource.Collection(queryset=queryset, *args, **kwargs);

json_MarketingCampaign_resource = collection(
    queryset = MarketingCampaign.objects.all(),
)

json_CampaignFile_resource = collection(
    queryset = CampaignFile.objects.all(),
    receiver = FormReceiver()
)

json_CampaignFile_last_resource = collection(
    queryset = CampaignFile.objects.order_by('id').reverse()[:1]
)

json_RemoteDevice_resource = collection(
    queryset = RemoteDevice.objects.all()
)

json_DeviceRecord_resource = collection(
    queryset = DeviceRecord.objects.all()
)

json_RemoteBluetoothDeviceRecord_resource = collection(
    queryset = RemoteBluetoothDeviceRecord.objects.all()
)

json_RemoteBluetoothDeviceFoundRecord_resource = collection(
    queryset = RemoteBluetoothDeviceFoundRecord.objects.all()
)

json_RemoteBluetoothDeviceSDP_resource = collection(
    queryset = RemoteBluetoothDeviceSDP.objects.all()
)

json_RemoteBluetoothDeviceNoSDP_resource = collection(
    queryset = RemoteBluetoothDeviceNoSDP.objects.all()
)

json_RemoteBluetoothDeviceSDPTimeout_resource = collection(
    queryset = RemoteBluetoothDeviceSDPTimeout.objects.all()
)

json_RemoteBluetoothDeviceFilesRejected_resource = collection(
    queryset = RemoteBluetoothDeviceFilesRejected.objects.all(),
)

json_RemoteBluetoothDeviceFilesSuccess_resource = collection(
    queryset = RemoteBluetoothDeviceFilesSuccess.objects.all()
)

json_RemoteBluetoothDeviceFileTry_resource = collection(
    queryset = RemoteBluetoothDeviceFileTry.objects.all()
)

def grab_file(request, pk):
    f = CampaignFile.objects.get(pk=pk).file
    mime = guess_mime(f.name)
    return HttpResponse(f.read(), mimetype=mime[0])

def index(request):
    return HttpResponse("REST interface, you're providing a bad url")
