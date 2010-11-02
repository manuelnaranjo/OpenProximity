"this is the locale selecting middleware that will look at accept headers"

from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.middleware.locale import LocaleMiddleware

class ILocaleMiddleware(object):
    def process_request(self, request):
	try:
	    super(ILocaleMiddleware, self).process_request(request)
	except:
	    pass
