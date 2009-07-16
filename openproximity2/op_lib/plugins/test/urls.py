from django.conf.urls.defaults import *
from django.http import HttpResponse
from django.views.generic.simple import direct_to_template

import views

urlpatterns = patterns( '',
	(r'^template', direct_to_template, {'template': 'test/hello.html', }
	(r'.*', views.index ),
    )
