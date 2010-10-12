import re
from django import http, template
from django.contrib.auth import authenticate, login
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.views.decorators.cache import never_cache
from django.conf import settings

from django_restapi import resource as resources
from django_restapi import model_resource
from django_restapi import responder

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class RestSite(object):
    """
    An RestSite object encapsulates an instance of the Django rest application, ready
    to be hooked in to your URLconf. Resources are registered with the RestSite using the
    register() method, and the urls variable can then be used as a Django view function
    that presents a full rest interface for the collection of registered resources.
    
    If API is set to True then it will try generating the API pages.
    """

    index_template = None
    login_template = None
    app_index_template = None

    def __init__(self, name=None, app_name='rest', api=True):
        self._registry = [] # resources registry 
        self.root_path = None
        if name is None:
            self.name = 'rest'
        else:
            self.name = name
        self.app_name = app_name
        self.API = True

    def register(self, resource, *args, **kwargs):
        """
        Registers the given resource.

        The resource should be Resource classes, not instances. If you pass a Model class
        then a collection resource is created automatically.

        If a resource is already registered, this will raise AlreadyRegistered.
        """
        if not isinstance(resource, resources.ResourceBase):
            resource = model_resource.Collection( model = resource, *args, **kwargs )

        resource.api = self.API
        resource.site = self

        if resource in self._registry:
            raise AlreadyRegistered('The resource %s is already registered' % resource.__name__)

        # Instantiate the rest class to save in the registry
        self._registry.append(resource)

    def unregister(self, resource):
        """
        Unregisters the given resource.

        If a resource isn't already registered, this will raise NotRegistered.
        """
        if resource not in self._registry:
            raise NotRegistered('The resource %s is not registered' % resource.__name__)
        resource.site = None
        del self._registry[resource]

    def rest_view(self, view, cacheable=False):
        """
        Decorator to create an rest view attached to this ``RestSite``. 

        You'll want to use this from within ``RestSite.get_urls()``:

            class MyRestSite(RestSite):

                def get_urls(self):
                    from django.conf.urls.defaults import patterns, url

                    urls = super(MyRestSite, self).get_urls()
                    urls += patterns('',
                        url(r'^my_view/$', self.rest_view(some_view))
                    )
                    return urls

        By default, rest_views are marked non-cacheable using the
        ``never_cache`` decorator. If the view can be safely cached, set
        cacheable=True.
        """
        def inner(request, *args, **kwargs):
            return view(request, *args, **kwargs)
        if not cacheable:
            inner = never_cache(inner)
        return update_wrapper(inner, view)
        
    def get_url(self):
	return resolve('%s:index' % self.name)

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url, include

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.rest_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # Rest-site-wide views.
        urlpatterns = patterns('',
            url(r'^$',
                wrap(self.index),
                name='index'),
        )

        # Add in each model's views.
        for resource in self._registry:
            urlpatterns += patterns('',
                url(r'^%s/' % (resource.baseurl), 
            	    include(resource.urls, namespace=resource.name, app_name=self.app_name)
            	))
        return urlpatterns

    def urls(self):
        return self.get_urls(), self.app_name, self.name
    urls = property(urls)

    def index(self, request, extra_context=None):
        """
        Displays the main rest index page, which lists all of the installed
        apps that have been registered in this site, only if API is set to True
        """
        if not self.API:
            return http.HttpResponseForbidden("API not enabled.")

        if not self.root_path:
            self.root_path = reverse('%s:index' % self.app_name)

        resource_dict = {}
        for resource in self._registry:
            resource_dict[capfirst(resource.name)] = {
        	'name': resource.name,
                'rest_url': mark_safe('%s/' % resource.baseurl),
                'api_url': mark_safe('%s/API/' % resource.baseurl)
            }

        context = {
            'title': _('Rest API'),
            'resource_dict': resource_dict.itervalues(),
            'root_path': self.root_path,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.index_template or 'rest/index.html', context,
            context_instance=context_instance
        )
    index = never_cache(index)

# This global object represents the default rest site, for the common case.
# You can instantiate RestSite in your own code to create a custom rest site.
site = RestSite()
