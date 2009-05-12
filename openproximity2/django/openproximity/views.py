# Create your views here.
from django.http import HttpResponse

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import get_template
from django.template import Context
from django.views.generic import list_detail

from models import *

def add_record_accepted(request):    
    return HttpResponse('Recorded\n')

def add_record(request):
    if not request.method == 'POST':
	raise Http404("I only undertand POST")
    
    print request.POST
    
    time = request.POST.get('time', None)
    address_ = request.POST.get('address', None)
    action_ = request.POST.get('action', None)
    action_extra = request.POST.get('action_extra', None)
    server_address_ = request.POST.get('server_address', None)
    
    if address_ is None or action_ is None:
	raise Http404("Missing required arguments")
    
    record = DeviceRecord()
    record.action = get_object_or_404(RemoteBluetoothAction, short_name=action_)
    
    if server_address_ is not None:
	try:
	    record.dongle = BluetoothDongle.objects.get(address__exact=server_address_)
	except:
	    pass	    
    
    if time is not None:
	record.time = time
    record.address = address_
    record.action_extra = action_extra
    
    record.save()
    
    return HttpResponse('Recorded\n')
