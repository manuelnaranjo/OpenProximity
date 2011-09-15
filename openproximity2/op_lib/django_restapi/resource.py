# -*- coding: utf-8 -*-
"""
Generic resource class.
"""
from django.utils.translation import ugettext as _
from authentication import NoAuthentication
from django.core.urlresolvers import reverse as reverse
from django.http import Http404, HttpResponse, HttpResponseNotAllowed
from django import template
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache

def load_put_and_files(request):
    """
    Populates request.PUT and request.FILES from
    request.raw_post_data. PUT and POST requests differ 
    only in REQUEST_METHOD, not in the way data is encoded. 
    Therefore we can use Django's POST data retrieval method 
    for PUT.
    """
    if request.method == 'PUT':
        request.method = 'POST'
        request._load_post_and_files()
        request.method = 'PUT'
        request.PUT = request.POST
        del request._post

class HttpMethodNotAllowed(Exception):
    """
    Signals that request.method was not part of
    the list of permitted methods.
    """

class ResourceBase(object):
    """
    Base class for both model-based and non-model-based 
    resources.
    """
    def __init__(self, authentication=None, permitted_methods=None):
        """
        authentication:
            the authentication instance that checks whether a
            request is authenticated
        permitted_methods:
            the HTTP request methods that are allowed for this 
            resource e.g. ('GET', 'PUT')
        """
        # Access restrictions
        if not authentication:
            authentication = NoAuthentication()
        self.authentication = authentication

        if not permitted_methods:
            permitted_methods = ["GET"]
        self.permitted_methods = [m.upper() for m in permitted_methods]

        self.api_index_template = None
        self.api = False
    
    def dispatch(self, request, target, *args, **kwargs):
        """
        """
        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            raise HttpMethodNotAllowed
        
        if request_method == 'GET':
            return target.read(request, *args, **kwargs)
        elif request_method == 'POST':
            return target.create(request, *args, **kwargs)
        elif request_method == 'PUT':
            load_put_and_files(request)
            return target.update(request, *args, **kwargs)
        elif request_method == 'DELETE':
            return target.delete(request, *args, **kwargs)
        else:
            raise Http404

    def get_url(self):
        """
        Returns resource URL.
        """
        url = reverse('%s:index' % (self.site.name), current_app=self.site.name)
        url += '%s/' % self.baseurl
        return url

    def getAPI(self, request, extra_context=None):
        if not self.api:
            raise Exception("API generation not enabled")
        
        context = {
                   'title': _('Rest API for %s' % self.name),
                   'resource': self,
                   'root_path': self.site.root_path
        }
        
        if getattr(self, 'generateAPI', None):
            context.update(self.generateAPI())
        
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.api_index_template or 'rest/api_index.html', context,
                context_instance=context_instance)

    getAPI = never_cache(getAPI)

    def name(self):
        raise NotImplementedError
    name = property(name)

    def baseurl(self):
        raise NotImplementedError
    baseurl = property(baseurl)

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url

        out =  patterns('',)
        if self.api:
            out+= patterns('', 
                url (r'^API/$', self.getAPI, name="API") 
            )
        out+= patterns('', 
            url(r'^([^/]*)/?$', self, name="index") 
        )
        return out

    def urls(self):
        return self.get_urls()
    urls = property(urls)

    # The four CRUD methods that any class that 
    # inherits from Resource may implement:
    
    def create(self, request):
        raise Http404
    
    def read(self, request):
        raise Http404
    
    def update(self, request):
        raise Http404
    
    def delete(self, request):
        raise Http404

class Resource(ResourceBase):
    """
    Generic resource class that can be used for
    resources that are not based on Django models.
    """
    def __init__(self, authentication=None, permitted_methods=None,
                 mimetype=None):
        """
        authentication:
            the authentication instance that checks whether a
            request is authenticated
        permitted_methods:
            the HTTP request methods that are allowed for this 
            resource e.g. ('GET', 'PUT')
        mimetype:
            if the default None is not changed, any HttpResponse calls 
            use settings.DEFAULT_CONTENT_TYPE and settings.DEFAULT_CHARSET
        """
        ResourceBase.__init__(self, authentication, permitted_methods)
        self.mimetype = mimetype
    
    def __call__(self, request, *args, **kwargs):
        """
        Redirects to one of the CRUD methods depending 
        on the HTTP method of the request. Checks whether
        the requested method is allowed for this resource.
        """
        # Check permission
        if not self.authentication.is_authenticated(request):
            response = HttpResponse(_('Authorization Required'), mimetype=self.mimetype)
            challenge_headers = self.authentication.challenge_headers()
            for k,v in challenge_headers.items():
                response[k] = v
            response.status_code = 401
            return response
        
        try:
            return self.dispatch(request, self, *args, **kwargs)
        except HttpMethodNotAllowed:
            response = HttpResponseNotAllowed(self.permitted_methods)
            response.mimetype = self.mimetype
            return response
    
