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

from django.conf.urls.defaults import *

from admin import myadmin

import views

urlpatterns = patterns( '',
	url(r'^admin/', include(myadmin.get_urls()), name="camera-admin"),
	url(r'^API/camera/list', views.API_camera_list),
	url(r'^API/camera/latest_picture/(?P<address>([a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2})', views.API_camera_last_picture),
	url(r'^grab/picture/(?P<filename>.*)', views.grab_picture),
	url(r'^grab/latest/(?P<addr>[0-9a-fA-F]{12})\.jpg', views.grab_latest_by_camera),
	url(r'^stream/(?P<addr>[0-9a-fA-F]{12})', views.stream_mode),
	url(r'^latest-picture/', views.latest_picture),
	url(r'^$', views.index, name="camera-index"),
    )
