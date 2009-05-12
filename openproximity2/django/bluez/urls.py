from django.conf.urls.defaults import *
from django.views.generic import list_detail

import views

urlpatterns = patterns('',
    (r'state/(?P<path>.+)', views.status_hci),
    (r'^$', views.index),
)
