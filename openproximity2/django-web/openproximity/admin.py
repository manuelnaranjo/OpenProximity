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
from models import *
from django.contrib import admin


class CampaignRuleAdmin(admin.ModelAdmin):
    fieldsets = (
	(None, {
	    'fields': ('service', 'files', 'rejected_count','tries_count'),
	}),
	('Timing Filters', {
	    'classes': ('collapse', ),
	    'fields': ('start', 'end')
	}),
	('Extra Filter Settings', {
	    'classes': ('collapse', ),
	    'fields': ('name_filter', 'addr_filter', 'devclass_filter')
	}),
    )

admin.site.register(RemoteScannerBluetoothDongle)
admin.site.register(ScannerBluetoothDongle)
admin.site.register(UploaderBluetoothDongle)
admin.site.register(BluetoothDongle)

admin.site.register(CampaignRule, CampaignRuleAdmin)
admin.site.register(MarketingCampaign)
admin.site.register(CampaignFile)
