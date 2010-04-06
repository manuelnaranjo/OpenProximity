#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009 Naranjo Manuel Francisco <manuel@aircable.net>
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

from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import render_to_response

class AlreadyRegistered(Exception):
    pass

class TweetSite(object):
    """
        A tweet site
    """
    
    def __init__(self, klass, field="pk", convert=int):
        '''
            Creates a new TweetSite.
            arguments:
                klass: which class to use
                field: which field to use for sorting
                convert: converting function when using non integers variables
        '''
        self.klass = klass
        self.field = field
        self.convert = convert
        
        from django.conf.urls.defaults import patterns, url, include
        
        self.urlpatterns = patterns( '',
            url(r'^latest/', self.latest_view),
            url(r'^posts/', self.posts_view),
            url(r'.*', self.index_view), 
        )

    def latest_view(self, request):
        """
            This view will return which is the latest entry in the table.
        """
        data = serializers.serialize('json',(self.klass.objects.latest('pk'),))
        return HttpResponse(data, mimetype="application/json")
        

    def posts_view(self, request):
        """
            This view will return a json array with the latest posts
        """
        
        pk = request.GET.get('pk', None)
        amount = int(request.GET.get('amount', 10))
        
        qs = self.klass.objects.all()
        
        if pk is not None:
            pk = self.convert(pk)
            
            filt = { '%s__gt' % self.field: pk }
        
            qs = qs.filter(**filt)
        qs = qs.order_by('-%s' % self.field)
        
        data = serializers.serialize('json', qs[:amount])
        
        return HttpResponse(data, mimetype="application/json")
        
    def index_view(self, request):
        return render_to_response( 'microblog/base.html',{})
