from django.conf.urls.defaults import *

from django.http import HttpResponse

from views import index

def hello(request, argument="/"):
    return HttpResponse("Hello world, you called me from %s" % argument)

urlpatterns = patterns( '',
	(r'(?P<argument>+*)', hello ),
	(r'.*', index),
    )
