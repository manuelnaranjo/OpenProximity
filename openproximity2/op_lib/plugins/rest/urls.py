from django.conf.urls.defaults import patterns, include
import django_restapi as restapi

restapi.autodiscover()
import rest

urlpatterns = patterns ('',
    # Uncomment the next line to enable the admin:
    (r'', include(restapi.site.urls)),
)
