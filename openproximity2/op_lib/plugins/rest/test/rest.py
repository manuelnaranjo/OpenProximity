#!/usr/bin/python
import urllib2, json

username='admin'
password='aircable'

class RESTRequest(urllib2.Request):
    def __init__(self, method='GET', *args, **kwargs):
	self._method=method
        assert self._method in ['GET', 'POST', 'PUT', 'DELETE']
	urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
	return self._method

def login(url):
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    # this creates a password manager
    
    passman.add_password(None, url, username, password)
    # because we have put None at the start it will always
    # use this username/password combination for  urls
    # for which `theurl` is a super-url

    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    # create the AuthHandler

    opener = urllib2.build_opener(authhandler)

    urllib2.install_opener(opener)
    # All calls to urllib2.urlopen will now use our handler
    # Make sure not to include the protocol in with the URL, or
    # HTTPPasswordMgrWithDefaultRealm will be very confused.
    # You must (of course) use it when fetching the page though.

def __process(request):
    return urllib2.urlopen(request).read()

def list(url, klass):
    b = RESTRequest(url='%s/REST/%s/' % (url, klass))
    return __process(b)

def get(url, klass, pk):
    b = RESTRequest(url='%s/REST/%s/%s/' % (url, klass, pk))
    return __process( b )

def post(url=None, klass=None, data=None, *args, **kwargs):
    b = RESTRequest(url='%s/REST/%s/' % (url, klass), 
	method='POST',
	data=data, *args, **kwargs)
    return __process(b)

def put(url, klass, pk, data, *args, **kwargs):
    b = RESTRequest(url='%s/REST/%s/%s/' % (url, klass, pk), 
	method='PUT',
	data=data, *args, **kwargs)
    return __process(b)

def delete(url, klass, pk):
    b = RESTRequest(url='%s/REST/%s/%s/' % (url, klass, pk), method='DELETE')
    return __process(b)
