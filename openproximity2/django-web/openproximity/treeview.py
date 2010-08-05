#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010 Naranjo Manuel Francisco <manuel@aircable.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# Create your views here.

# imports from stdlib
from re import compile
from datetime import datetime
from mimetypes import guess_type as guess_mime
import rpyc, os, time

# imports from django
from django.db import models as mod
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template
from django.utils import simplejson
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.views.generic import list_detail
from django.contrib.admin.views import decorators
from django.conf import settings
import django.conf.urls.defaults as urls

# imports from aircable libs
from net.aircable.openproximity.pluginsystem import pluginsystem
from net.aircable.utils import logger, get_subclass, get_subclasses

# imports from op libs
import models

class Node(object):
    '''
    A wrapper class for easily creating an ajax node.
    '''
    def __init__(self, id, data, state="closed", klass=None):
        self.id = id
        self.data = data
        self.state = state
        self.klass = klass
    
    def getDict(self):
        out = {
            "attributes": { 
                "id": self.id 
            },
            "data": self.data
        }
        if self.state: out['state'] = self.state
        if self.klass: out["attributes"]['class'] = self.klass
        return out

# urls or ids can be of two forms:
# AppLabel_ModuleName_pk
# AppLabel_ModuleName_RelatedField_RelatedPk
# AppLabel_ModuleName_RelatedField_RelatedPk, minPk, maxPk
def generic_URL(*args):
    return "_".join( str(k) for k in args)

def URL(obj):
    return generic_URL(obj._meta.app_label, obj._meta.module_name, obj.pk)

def URL_RELATED(klass, field_name, related):
    return generic_URL(
        klass._meta.app_label, klass._meta.module_name,
        field_name, related.pk)

class ModelNode(object):
    def __init__(self, obj):
        self.node = Node( 
            URL(obj), 
            "%s: %s" %(obj._meta.object_name, str(obj)),
            klass="deletable" if getattr(obj, 'deletable', None) else None
        ).getDict()

        self.node['children'] = [ 
            Node( 
                URL(obj)+"_"+o.name, 
                "%s: %s" % (o.name, getattr(obj, o.name)),
                None
            ).getDict() 
            for o in obj._meta.fields if not o.rel
        ]

        self.node['children'].extend([ 
                Node( URL(getattr(obj, o.name)), o.name ).getDict() 
                for o in obj._meta.fields if o.rel
        ])
    
        for related in obj._meta.get_all_related_objects():
            p = {"%s__pk" % related.field.name: obj.pk}
            if related.model.objects.filter(**p).count() > 0:
                for subk in get_subclasses(related.model):
                    qs = subk.objects.filter(**p)
                    if qs.count() > 1:
                        self.node['children'].append( 
                            Node(
                                URL_RELATED(subk, related.field.name, obj),
                                    "%s: %s items" % (
                                        subk._meta.object_name,
                                        qs.count())
                            ).getDict()  
                        )
                    elif qs.count() == 1:
                        self.node['children'].append( 
                            ModelNode(qs.get()).getDict() )
    def getDict(self):
        return self.node

class RelatedNode(object):
    def __init__(self, qs, app, model, related_field, related_pk):
        out = []
        out.append(
            Node(
                "_".join([app, model, related_field, 'count']),
                "Count: %s" % qs.count(),
                None
                ).getDict()
        )

        prev = None
        i=0
        j=0
        step = 200
    
        for curr in qs[::step]:
            if prev:
                url = generic_URL(app, model, related_field, related_pk, prev, 
                    curr.pk)
                title = "From %s to %s" % (i+1, j)
                out.append( Node(url, title).getDict() )

            i=j
            j+=step
            prev=curr.pk
    
        curr = qs[qs.count()-1].pk
        url = generic_URL(app, model, related_field, related_pk, prev, curr+1)
        title = "From %s to %s" % (i+1, qs.count())
        out.append( Node(url, title).getDict())
        self.children = out
    
    def getDict(self):
        return self.children


def modelList(request, klass, subclass=False):
    kl = None
    if getattr(klass, 'deletable', False):
        kl = "deletable"

    for o in klass.objects.all():
        o = get_subclass(o) if subclass else o
        yield Node( URL(o), str(o), klass=kl ).getDict()

def modelDetail(request, app, model, pk):
    o = mod.get_model(app, model).objects.get(pk=pk)
    return HttpResponse( 
        simplejson.dumps(ModelNode(o).getDict()['children']), 
        content_type="application/json")

def relatedDetail(request, app, model, rel_field, rel_pk):
    qs = mod.get_model(app, model).objects.all()
    req = {str("%s__pk" % rel_field): int(rel_pk)}
    qs = qs.filter(**req)

    return HttpResponse( 
        simplejson.dumps(RelatedNode(qs, app, model, rel_field, rel_pk)
                .getDict()), 
        content_type="application/json")

def relatedDetailSubQuery(request, app, model, rel_field, rel_pk, min_pk, max_pk):
    qs = mod.get_model(app, model).objects.all()
    req = {
        str("%s__pk" % rel_field): int(rel_pk),
        "pk__gte": int(min_pk),
        "pk__lt": int(max_pk),
    }
    qs = qs.filter(**req)

    return HttpResponse( 
        simplejson.dumps( [ ModelNode(get_subclass(o)).getDict() for o in qs] ), 
        content_type="application/json")

def wrapper(generator, *args, **kwargs):
    return HttpResponse(
        simplejson.dumps(list(generator(*args, **kwargs))),
        content_type="application/json")

def initialData(request):
    out = [
        Node("remote_devices", _("Remote Devices")).getDict(),
        Node("campaigns", _("Campaigns")).getDict(),
        Node("scanner_dongles", _("Scanner Dongles")).getDict(),
        Node("uploader_dongles", _("Uploader Dongles")).getDict(),
        Node("all_dongles", _("All Dongles")).getDict()
    ]

    return HttpResponse(
        simplejson.dumps(out),
        content_type="application/json")


DATA={
    'remote_devices': lambda x: wrapper(modelList, x, models.RemoteDevice),
    'campaigns': lambda x: wrapper(modelList, x, models.MarketingCampaign),
    'scanner_dongles': lambda x: wrapper(modelList, x, models.ScannerBluetoothDongle),
    'uploader_dongles': lambda x: wrapper(modelList, x, models.UploaderBluetoothDongle),
    'all_dongles': lambda x: wrapper(modelList, x, models.BluetoothDongle, True),
}

def data(request):
    id_ = request.POST.get('id', '').lower()
    logger.debug("treeview.data %s" % id_)
    
    if id_ in DATA:
        return DATA.get(id_)(request)
    spl = id_.split('_')
    
    if len(spl) == 3:       # we got a request for certain device
        logger.debug("model detail %s" % spl)
        return modelDetail(request, *spl)
    elif len(spl) == 4:
        logger.debug("related model detail %s" % spl)
        return relatedDetail(request, *spl)
    elif len(spl) == 6:
        logger.debug("related model detail subquery %s" % spl)
        return relatedDetailSubQuery(request, *spl)

    return initialData(request)

def delete(request):
    if request.method != 'POST':
	raise Exception("Expected a POST")

    if not request.user.is_authenticated() or not request.user.is_staff:
	return HttpResponse(
    	    simplejson.dumps(
    		{
    		    'need_login': True, 
    		}),
    	    content_type="application/json")

    app, model, pk = request.POST.get('id').split('_')
    o = mod.get_model(app, model).objects.get(pk=pk)
    o.delete()
    return HttpResponse(
        simplejson.dumps(
    	    {
    		'deleted': True, 
    		'pk': pk, 
    		'app': app,
    		'model': model
    	    }),
        content_type="application/json")

def index(request):
    return render_to_response("op/treeview.html")

urlpatterns = urls.patterns('',
    (r'delete', delete),
    (r'data', data),
    (r'', index),
)

