# -*- coding: utf-8 -*-
"""
Model-bound resource class.
"""
from django import forms
from django.conf.urls.defaults import patterns
from django.http import *
from django.forms import ModelForm, models
from django.forms.util import ErrorDict
from django.utils.functional import curry
from django.utils.translation.trans_null import _
from django.utils.safestring import mark_safe
from resource import ResourceBase, load_put_and_files, reverse, HttpMethodNotAllowed
from receiver import InteligentReceiver
import responder as responders

class InvalidModelData(Exception):
    """
    Raised if create/update fails because the PUT/POST 
    data is not appropriate.
    """
    def __init__(self, errors=None):
        if not errors:
            errors = ErrorDict()
        self.errors = errors

class Collection(ResourceBase):
    """
    Resource for a collection of models (queryset).
    """
    def __init__(self, model, queryset=None, responder=None, receiver=None, 
                 authentication=None, permitted_methods=None, expose_fields=None, 
                 entry_class=None, form_class=None, api=False, baseurl=None):
        """
        model:
            model to use for this collection
        queryset:
            determines the subset of objects that make up this resource
        responder:
            the data format instance that creates HttpResponse
            objects from single or multiple model objects and
            renders forms, default uses a smart method based on the
            accept header.
        receiver:
            the data format instance that handles POST and
            PUT data
        authentication:
            the authentication instance that checks whether a
            request is authenticated
        permitted_methods:
            the HTTP request methods that are allowed for this 
            resource e.g. ('GET', 'PUT')
        expose_fields:
            the model fields that can be accessed
            by the HTTP methods described in permitted_methods
        entry_class:
            class used for entries in create() and get_entry();
            default: class Entry (see below)
        form_class:
            base form class used for data validation and
            conversion in self.create() and Entry.update()
        api:
            enable if you want API generation enabled.
        base_url:
            base url where this resource will be availabe.
        """
        
        # model to use
        self.model = model
        
        # Available data
        self.queryset = queryset or model.objects.all()  
        
        # Input format
        self.receiver = receiver or InteligentReceiver()

        # api        
        self.api = api
        
        # Input validation
        self.form_class = form_class or ModelForm
        
        # Output format / responder setup
        self.responder = responder or responders.InteligentResponder()
        self.expose_fields = expose_fields or [field.name for field in self.model._meta.fields]
        self.responder.expose_fields = self.expose_fields

        # this is used by template responder only
        if hasattr(self.responder, 'create_form'):
            self.responder.create_form = curry(responder.create_form, queryset=queryset, form_class=form_class)
        if hasattr(self.responder, 'update_form'):
            self.responder.update_form = curry(responder.update_form, queryset=queryset, form_class=form_class)

        # Resource class for individual objects of the collection
        self.entry_class = entry_class or Entry
        
        self._base_url = baseurl

        ResourceBase.__init__(self, authentication, permitted_methods)

    def baseurl(self):
        if not getattr(self, '_base_url', None):
            meta = self.model._meta
            self._base_url = "%s/%s" % (meta.app_label, meta.module_name)
        return self._base_url
    baseurl = property(baseurl)

    def name(self):
        if not getattr(self, '_name', None):
            meta = self.model._meta
            self._name = "%s_%s" % (meta.app_label, meta.module_name)
        return self._name
    name = property(name)

    def form(self):
        if not getattr(self, '_form', None):
            self._form = models.modelform_factory(self.model, form=self.form_class)
        return self._form
    form=property(form)

    def generateAPI(self):
        def internal_generate_api():
            for f_name in self.expose_fields:
                field = self.model._meta.get_field(f_name)
                yield field
        out = {}
        out['form'] = self.form()
        out['fields'] = internal_generate_api()
        return out

    def __call__(self, request, *args, **kwargs):
        """
        Redirects to one of the CRUD methods depending 
        on the HTTP method of the request. Checks whether
        the requested method is allowed for this resource.
        Catches errors.
        """
        # Check authentication
        if not self.authentication.is_authenticated(request):
            response = self.responder.error(request, 401)
            challenge_headers = self.authentication.challenge_headers()
            for k,v in challenge_headers.items():
                response[k] = v
            return response
        
        # Remove queryset cache
        self.queryset = self.queryset._clone()
        
        # Determine whether the collection or a specific
        # entry is requested. If not specified as a keyword
        # argument, assume that any args/kwargs are used to
        # select a specific entry from the collection.
        if kwargs.has_key('is_entry'):
            is_entry = kwargs.pop('is_entry')
        else:
            eval_args = tuple([x for x in args if x != ''])
            is_entry = bool(eval_args or kwargs)
        
        # Redirect either to entry method
        # or to collection method. Catch errors.
        try:
            if is_entry:
                entry = self.get_entry(*args, **kwargs)
                return self.dispatch(request, entry)
            else:
                return self.dispatch(request, self)
        except HttpMethodNotAllowed:
            response = self.responder.error(request, 405)
            response['Allow'] = ', '.join(self.permitted_methods)
            return response
        except (self.queryset.model.DoesNotExist, Http404):
            return self.responder.error(request, 404)
        except InvalidModelData, i:
            return self.responder.error(request, 400, i.errors)
        
        # No other methods allowed: 400 Bad Request
        return self.responder.error(request, 400)
    
    def create(self, request):
        """
        Creates a resource with attributes given by POST, then
        redirects to the resource URI. 
        """
        # Create form filled with POST data
        ResourceForm = models.modelform_factory(self.queryset.model, form=self.form_class)
        data = self.receiver.get_post_data(request)
        try:
            files = self.receiver.get_data(request, 'FILES')
        except:
            files = {}
        form = ResourceForm(data, files)
        
        # If the data contains no errors, save the model,
        # return a "201 Created" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if form.is_valid():
            new_model = form.save()
            model_entry = self.entry_class(self, new_model)
            response = model_entry.read(request)
            response.status_code = 201
            response['Location'] = model_entry.get_url()
            return response

        # Otherwise return a 400 Bad Request error.
        raise InvalidModelData(form.errors)
    
    def read(self, request):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        return self.responder.list(request, self.queryset)
    
    def get_entry(self, pk_value):
        """
        Returns a single entry retrieved by filtering the 
        collection queryset by primary key value.
        """
        instance = self.queryset.get(**{self.model._meta.pk.name : pk_value})
        entry = self.entry_class(self, instance)
        return entry

class Entry(object):
    """
    Resource for a single model.
    """
    def __init__(self, collection, model):
        self.collection = collection
        self.model = model

    def get_url(self):
        """
        Returns the URL for this resource object.
        """
        pk_value = getattr(self.model, self.model._meta.pk.name)
        return '%s%s/' % (self.collection.get_url(), pk_value)
#        #,  (pk_value,))
#        #mark_safe('%s/%s/' % (reverse(self.collection), pk_value))

    def create(self, request):
        raise Http404

    def read(self, request):
        """
        Returns a representation of a single model.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the resource URI with method GET.
        """
        return self.collection.responder.element(request, self.model)

    def update(self, request):
        """
        Changes the attributes of the resource identified by 'ident'
        and redirects to the resource URI. Usually called by a HTTP
        request to the resource URI with method PUT.
        """
        # Create a form from the model/PUT data
        ResourceForm = models.modelform_factory(self.model.__class__, form=self.collection.form_class)
        data = self.collection.receiver.get_put_data(request)
        try:
            files = self.receiver.get_data(request, 'FILES')
        except:
            files = {}
        form = ResourceForm(data, files, instance=self.model)


        # If the data contains no errors, save the model,
        # return a "200 Ok" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if form.is_valid():
            form.save()
            response = self.read(request)
            response.status_code = 200
            response['Location'] = self.get_url()
            return response

        # Otherwise return a 400 Bad Request error.
        raise InvalidModelData(form.errors)

    def delete(self, request):
        """
        Deletes the model associated with the current entry.
        Usually called by a HTTP request to the entry URI
        with method DELETE.
        """
        self.model.delete()
        return HttpResponse(_("Object successfully deleted."), self.collection.responder.mimetype)


