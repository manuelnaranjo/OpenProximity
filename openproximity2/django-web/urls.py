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
from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout
from net.aircable.utils import logger

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

import os

from net.aircable.openproximity.pluginsystem import pluginsystem

admin.autodiscover()

urlpatterns = patterns ('',
    (r'accounts/login', login, {'template_name': 'op/login.html'}),
    (r'accounts/logout', logout),

    # include needed interfaces    
#    (r'^bluez/', include('bluez.urls')),
    (r'^openproximity/', include('openproximity.urls')),
    
    #include translation site
    (r'^admin/translate/', include('rosetta.urls'),{},"translate"),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
#    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls),{},"admin"),
    
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        {       'document_root': os.path.join(os.path.dirname(__file__), 'media')},
        "site-media"
    ),
    
    (r'^notification/', include('notification.urls'),{},"notification"),
)

for plugin in pluginsystem.get_plugins('urls'):
    logger.info("%s provides urls" % plugin.provides.get('name', plugin.name))
    url, path = plugin.provides.get('urls')
    urlpatterns += patterns( '', 
        (r'^%s/' % url, 
            include('%s.%s' % ( plugin.name, path)),
            {},
            plugin.name # allow url to be reverse resolved
    ))

urlpatterns += patterns('', 
    (r'', include('openproximity.urls'),{},"openproximity")
)

