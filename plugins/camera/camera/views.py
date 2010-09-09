#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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

from django import forms
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.template import RequestContext
from django.shortcuts import render_to_response
from mimetypes import guess_type as guess_mime
from wadofstuff.django.serializers.base import Serializer
import models, http
from net.aircable.utils import logger
from select import select
import fcntl, os

SET = settings.OPENPROXIMITY.getAllSettings()

def API_camera_list(request):
    b = models.CameraRemoteDevice.objects.all().values('name', 'address')
    return HttpResponse(json.dumps(list(b)), 'application/json')

def stream_mode(request, addr):
    address = ':'.join([ addr[i*2:i*2+2] for i in range(len(addr)/2) ])
    def internal_stream():
	print "internal_stream"
	try:
	    print '/tmp/camera_%s.pipe' % address
	    fd = open('/tmp/camera_%s.pipe' % address, 'rb')
	    print "open pipe"
	except Exception, err:
	    print err
	    raise StopIteration()

	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
	
	while True:
	    r, x = select([fd,], [], [fd,])[::2]
	    if len(x) > 0:
		raise StopIteration()
	    b = fd.read()
	    if len(b) == 0:
		raise StopIteration()
	    yield 'image/jpeg', b

    return http.StreamingMultipartHttpResponse(internal_stream(), 
	    type="multipart/x-mixed-replace")

def API_camera_last_picture(request, address):
    b = models.CameraRecord.objects.filter(remote__address=address).latest('time')
    b = b.picture.name
    return HttpResponse( json.dumps(b), 'application/json')

def latest_picture(request):
    try:
	b = models.CameraRecord.objects.latest('time').picture.name
    except:
	b = None
    logger.info(b)
    return HttpResponse( json.dumps({'name': b}), 'application/json')

def grab_picture(request, filename):
    f=models.CameraRecord.objects.get(picture=filename).picture
    mime = guess_mime(f.name)
    logger.info(f.name)
    return HttpResponse(f.read(), mimetype=mime[0])
    
def grab_latest_by_camera(request, addr):
    camera = ':'.join([ addr[i*2:i*2+2] for i in range(len(addr)/2) ])
    f = models.CameraRecord.objects.filter(remote__address=camera).latest('time').picture
    mime = guess_mime(f.name)
    logger.info('%s -> %s' % (camera, f.name))
    parts = [
	(mime[0], f.read())
    ]
    return http.StreamingMultipartHttpResponse(parts, 
	    type="multipart/x-mixed-replace")

def index(request):
    return render_to_response("camera/index.html", {},
	context_instance=RequestContext(request))
