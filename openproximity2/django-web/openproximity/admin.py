from models import *
from django.contrib import admin


class CampaignRuleAdmin(admin.ModelAdmin):
    fieldsets = (
	(None, {
	    'fields': ('service', 'files'),
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

admin.site.register(ScannerBluetoothDongle)
admin.site.register(UploaderBluetoothDongle)
admin.site.register(CampaignRule, CampaignRuleAdmin)
admin.site.register(MarketingCampaign)
admin.site.register(CampaignFile)
