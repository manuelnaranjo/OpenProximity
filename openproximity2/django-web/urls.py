from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'accounts/login', login),
    (r'accounts/logout', logout),

    # include needed interfaces    
    (r'^bluez/', include('bluez.urls')),
    (r'^openproximity/', include('openproximity.urls')),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	{	'document_root': os.path.join(os.path.dirname(__file__), 'media')}
    ),
    (r'', include('openproximity.urls')),
)
