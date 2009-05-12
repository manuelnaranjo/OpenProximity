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
        
        bluez_manager_obj = bus.get_object('org.bluez', '/org/bluez')
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
        adapter.GetAddress()
        
        if request.method=="POST":
    	    method=request.POST.get("method", None)
    	    args=request.POST.get("args", None)
    	    sleep=request.POST.get("sleep", None)
    	    
    	    print method, args
    	    
    	    if method is not None:
    		function=getattr(adapter, method)
    		if args is not None:
    		    function(args)
    		else:
    		    function()
    		if sleep is not None:
    		    time.sleep(int(sleep))
    		
    	known = ()    

        for dongle in adapter.ListRemoteDevices():
    	    a = dict()
    	    a['address'] = dongle
    	    a['name'] = adapter.GetRemoteName(dongle)
    	    a['trusted'] = adapter.HasBonding(dongle)!=0
    	    a['lastseen'] = adapter.LastSeen(dongle)
    	    a['lastused'] = adapter.LastUsed(dongle)
    	    try:
		a['pin_length'] = int(adapter.GetPinCodeLength(dongle))
    		a['version'] = adapter.GetRemoteVersion(dongle)
    		a['revision'] = adapter.GetRemoteRevision(dongle)
    		a['manufacturer'] = adapter.GetRemoteManufacturer(dongle)
    		a['company'] = adapter.GetRemoteCompany(dongle)
    		a['major'] = adapter.GetRemoteMajorClass(dongle)
    		a['minor'] = adapter.GetRemoteMinorClass(dongle)
    	    except Exception, err:
    		print "ListRemoteDevices: %s" % err
    	
    	    known+=(a,)
    	    

#        seen_today = ()
#        yesterday=time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime(time.time()-24*60*60))
#        print yesterday
#        seen_recently = None
#        try:
#    	    seen_recently = adapter.ListRecentRemoteDevices(yesterday)
#    	except Exception, err:
#    	    print "ListingRemoteDevices(%s): %s" %  (yesterday, err)
#    	else:
#    	    for dongle in seen_recently:
#    		print "today:%s" % dongle
#    		a = dict()
#    		a['address'] = dongle
#    		a['name'] = adapter.GetRemoteName(dongle)
#    		a['trusted'] = adapter.HasBonding(dongle)!=0
#    		a['lastseen'] = adapter.LastSeen(dongle)
#    		a['lastused'] = adapter.LastUsed(dongle)
#    		try:
#		    a['pin_length'] = int(adapter.GetPinCodeLength(dongle))
#    		    a['version'] = adapter.GetRemoteVersion(dongle)
#    		    a['revision'] = adapter.GetRemoteRevision(dongle)
#    		    a['manufacturer'] = adapter.GetRemoteManufacturer(dongle)
#    		    a['company'] = adapter.GetRemoteCompany(dongle)
#    		    a['major'] = adapter.GetRemoteMajorClass(dongle)
#    		    a['minor'] = adapter.GetRemoteMinorClass(dongle)
#    		except Exception, err:
#    		    print "RecentRemoteDevices: %s" % err
#    	
#    		seen_today+=(a,)

    except Exception, err:
	error = err

    return render_to_response("bluez/hci.html",
	{
	    
		'dbus': bus,
		'adapter': adapter,
		'error': error,
		'remotedevices': known, 
#		'remotedevices_today': seen_today,
	}
    )
