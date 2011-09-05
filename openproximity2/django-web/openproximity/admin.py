# -*- coding: utf-8 -*-
#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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
from django.utils.translation import ugettext as _
from timezones.utils import adjust_datetime_to_timezone
from timezones.zones import tz as TZ
from timezones.zones import PRETTY_TIMEZONE_CHOICES


class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')

admin.site.register(Setting, SettingAdmin)

class DongleAdmin(admin.ModelAdmin):
    list_display = ( 'address', 'name', 'enabled' )

class RemoteDongleAdmin(admin.ModelAdmin):
    list_display = ( 'address', 'name', 'local_dongle', 'priority', 'enabled' )

class RemoteDongleInline(admin.TabularInline):
    model = RemoteScannerBluetoothDongle
    fk_name = 'local_dongle'
    fields = ('address', 'name','priority', 'enabled')
    extra = 7
    template = 'op/tabular_remotescanner.html'
        
class ScannerDongleAdmin(admin.ModelAdmin):
    inlines = [ RemoteDongleInline ]
    list_display = ( 'address', 'name', 'priority', 'enabled' )

admin.site.register(ScannerBluetoothDongle, ScannerDongleAdmin)
admin.site.register(RemoteScannerBluetoothDongle, RemoteDongleAdmin)
admin.site.register(UploaderBluetoothDongle, DongleAdmin)

class CampaignFileAdmin(admin.StackedInline):
    model = CampaignFile
    date_hierarchy = None


class MarketingCampaignAdmin(admin.ModelAdmin):
    class Media:
        js = (
            "/site_media/js/jquery-1.6.2.min.js",
            "/site_media/js/Base.js",
            "/site_media/js/DateTime.js",
            "/site_media/js/date.js",
        )

    fieldsets = (
      (None, {
        'fields': ('name', 'enabled', 'service', 'pin_code'),
      }),
      ('Times filter',{
        'fields': ('rejected_count', 'rejected_timeout', 
            'tries_count', 'tries_timeout',
            'accepted_count')
      }),
      ('RSSI filter', {
        'fields': ('rssi_min', 'rssi_max'),
      }), 
      ('Dongles settings',{
        'fields': ('dongle_name',),
      }),
      ('Timing Filters', {
        'classes': ('collapse', ),
        'fields': ('start', 'end')
      }),
      ('Extra Filter Settings', {
        'classes': ('collapse', ),
        'fields': ('name_filter', 'addr_filter', 'devclass_filter')
      }),
      ('Expert Settings', {
        'classes': ('collapse', ),
        'fields': ('fixed_channel', 'concurrent_scanning', 'upload_on_discovered')
      }),
    )

    inlines = [ CampaignFileAdmin, ]

    list_display = ( 'name', 
        'service',
        'pin_code',
        'format_start',
        'format_end',
        'rssi_min',
        'rssi_max',
        'name_filter', 
        'addr_filter', 
        'devclass_filter',
        'enabled'
    )
    list_filter = ( 'service', 
        'start', 
        'end', 
        'rssi_min',
        'rssi_max',
        'name_filter', 
        'addr_filter',
        'devclass_filter',
        'enabled'
    )

    ordering = [ 'name', 'service', 'start', 'end', 'rssi_min', 'rssi_max' ]

    def save_model(self, request, obj, form, change):
        utz = request.user.get_profile().timezone
        if obj.start:
            obj.start = adjust_datetime_to_timezone(obj.start, utz, TZ)
        if obj.end:
            obj.end = adjust_datetime_to_timezone(obj.end, utz, TZ)
        obj.save()

    def change_view(self, request, object_id, extra_context=None):
        zone = request.user.get_profile().timezone.zone
        time_zone = dict(PRETTY_TIMEZONE_CHOICES)[zone][:10]
        my_context = {'time_zone': time_zone}
        return super(MarketingCampaignAdmin, self).\
            change_view(request,object_id,my_context)

    def changelist_view(self, request, extra_context=dict()):
        zone = request.user.get_profile().timezone.zone
        time_zone = dict(PRETTY_TIMEZONE_CHOICES)[zone][:10]
        extra_context['time_zone']=time_zone
        return super(MarketingCampaignAdmin, self).\
            changelist_view(request,extra_context)

    def __format(self, obj):
        return '<div class="datetimezulu">'+\
            obj.strftime("%Y-%m-%dT%H:%M:%SZ")+\
        '</div>'

    def format_start(self, obj):
        return self.__format(obj.start)
    format_start.short_description = _('Start')
    format_start.allow_tags=True

    def format_end(self, obj):
        return self.__format(obj.end)
    format_end.short_description = _('End')
    format_end.allow_tags=True


admin.site.register(MarketingCampaign, MarketingCampaignAdmin)
