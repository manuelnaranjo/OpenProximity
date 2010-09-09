# -*- coding: utf-8 -*-

from django.contrib import admin
import models

myadmin=admin.AdminSite()

myadmin.register(models.CameraBluetoothDongle)
myadmin.register(models.CameraRemoteDevice)
myadmin.register(models.CameraRecord)
myadmin.register(models.CameraCampaign)
