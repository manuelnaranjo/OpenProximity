from models import *
from django.contrib import admin

admin.site.register(BluetoothDongle)
admin.site.register(ScannerBluetoothDongle)
admin.site.register(UploaderBluetoothDongle)
admin.site.register(DeviceRecord)
admin.site.register(RemoteBluetoothDeviceRecord)
admin.site.register(RemoteBluetoothDeviceFoundRecord)
admin.site.register(MarketingCampaign)
admin.site.register(CampaignRule)
admin.site.register(CampaignFile)
admin.site.register(RemoteBluetoothDeviceSDP)
admin.site.register(RemoteBluetoothDeviceNoSDP)
admin.site.register(RemoteBluetoothDeviceSDPTimeout)
admin.site.register(RemoteBluetoothDeviceFileTry)
admin.site.register(RemoteBluetoothDeviceFilesRejected)
admin.site.register(RemoteBluetoothDeviceFilesSuccess)
#admin.site.register(Choice)
