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
# Create your views here.
import dbus as dbus
from django.shortcuts import render_to_response
import time

def index(request):
    bus = None
    manager = None
    manager_version = None
    error = None
    try:
	bus = dbus.SystemBus()	
        
        bluez_manager_obj = bus.get_object('org.bluez', '/')
        manager = dbus.Interface(bluez_manager_obj, 'org.bluez.Manager')
        adapter = manager.DefaultAdapter()
        
    except Exception, err:
	error = err

    return render_to_response("bluez/index.html",
	{
	    
		'dbus': bus,
		'manager': manager,
		'error': error,
	}
    )
    
def __parse_properties(items):
    out = dict()
    for key, val in items:
	try:
	    val=int(val)
	    if val == 0:
	        val = False
	    elif val == 1:
	        val = True
	    else:
	        val = '0x%s' % str(hex(val)).upper()[2:]
	except:
	    pass
	out[str(key)] = str(val)
    return out
	

def status_hci(request,path):
    bus = None
    manager = None
    manager_version = None
    error = None
    known = None
    try:
	bus = dbus.SystemBus()

        adapter_obj = bus.get_object('org.bluez', path)
        adapter = dbus.Interface(adapter_obj, 'org.bluez.Adapter')
	adapter.properties =  __parse_properties(adapter.GetProperties().iteritems())
        
        if request.method=="POST":
    	    method=request.POST.get("method", None)
    	    args=request.POST.get("args", None)
    	    sleep=request.POST.get("sleep", None)
	    prop_name=request.POST.get("name", None)
    	    prop_value=request.POST.get("value", None)
    	    
    	    if method is not None:
    		function=getattr(adapter, method)
		if method not in ['SetProperty',]:
    		    if args is not None:
    			function(args)
    		    else:
    			function()
		else:
		    function(prop_name, prop_value)
		
    		if sleep is not None:
    		    time.sleep(int(sleep))
    		
    	known = ()    

        for remote_path in adapter.ListDevices():
	    remote = dbus.Interface( bus.get_object('org.bluez', remote_path), 
		'org.bluez.Device')
	    remote.properties =  __parse_properties(remote.GetProperties().iteritems())
    	    known+=(remote,)

    except Exception, err:
	error = err

    return render_to_response("bluez/hci.html",
	{
	    
		'dbus': bus,
		'adapter': adapter,
		'properties': adapter.GetProperties(),
		'error': error,
		'remotedevices': known, 
	}
    )
