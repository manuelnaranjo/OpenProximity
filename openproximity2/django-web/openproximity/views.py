#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
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

from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template
from django.utils import simplejson
from django.utils.encoding import smart_str
from django.views.generic import list_detail
from django.contrib.admin.views import decorators

from django.conf import settings

from datetime import datetime
from net.aircable.openproximity.pluginsystem import pluginsystem
from net.aircable.utils import logger

from re import compile
from mimetypes import guess_type as guess_mime

from models import *
from forms import *
import rpyc, os, time

SET = settings.OPENPROXIMITY.getAllSettings()

def add_record_accepted(request):    
    return HttpResponse('Recorded\n')

def add_record(request):
    if not request.method == 'POST':
        raise Http404("I only undertand POST")
    
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
            record.dongle = BluetoothDongle.objects.get(
                    address__exact=server_address_)
        except:
            pass        
    
    record.time = time or None
    record.address = address_
    record.action_extra = action_extra
    record.save()
    
    return HttpResponse('Recorded\n')

AIRCABLE_MAC=['00:50:C2', '00:25:BF']
ADDRESS_MAC=compile("([0-9A-F]{2}\:){5}([0-9A-F]{2})")

def isAIRcable(address):
    return address[:8].upper() in AIRCABLE_MAC
    
def add_dongle(address, name, scanner, uploader, scanner_pri=1, uploader_max=7):
    logger.info("add_dongle %s %s %s %s %s %s" % 
        (address, name, scanner, uploader, scanner_pri, uploader_max)
    )
    search=ScannerBluetoothDongle.objects.filter(address=address)
    
    if scanner and search.count()==0:
        rec = ScannerBluetoothDongle()
        rec.address = address
        rec.name = name
        rec.priority = scanner_pri
        rec.enabled = True
        rec.save()
        logger.debug("scanner %s" % rec)
    
    if search.count()>0:
        rec=search.get()
        rec.enabled = scanner == True
        rec.priority = scanner_pri
        rec.save()
    
    search=UploaderBluetoothDongle.objects.filter(address=address)
    
    if uploader and search.count()==0:
        rec = UploaderBluetoothDongle()
        rec.address = address
        rec.name = name
        rec.max_conn = uploader_max
        rec.enabled = True
        rec.save()
        logger.debug("uploader %s" % rec)
    
    if search.count()>0:
        rec=search.get()
        rec.enabled = uploader == True
        rec.save()

@decorators.staff_member_required
def configure_campaign(request, name=None):
    logger.info("configure_campaign %s" % name)
    form = CampaignForm()
    logger.debug(form.as_table())

    return render_to_response('op/campaign_form.html',
        { 
            'form':  form,
        }, context_instance=RequestContext(request)
    )

@decorators.staff_member_required
def configure_dongle(request, address=None):
    logger.info("configure_dongle %s" % address)
    
    errors = []
    messages = []
    form = None
    if request.method == "POST":
        form=DongleForm(request.POST)
        if form.is_valid():
            cd=form.cleaned_data
            add_dongle(
                cd['address'],
                cd['name'],
                cd["scan"],
                cd["upload"],
                cd["scan_pri"],
                cd["upload_max"],
            )
            return HttpResponseRedirect('/')
            #messages.append("Dongle Configured")

    scanner = None
    scanner_pri = 1
    uploader = None
    uploader_max = 7
    
    name = "OpenProximity 2.0"
    
    search=BluetoothDongle.objects.filter(address=address)
    if search.count()>0:
        dongle = search.all()[0]
        name=dongle.name
    
    search=ScannerBluetoothDongle.objects.filter(address=address)
    if search.count() > 0:
        scanner = True
        scanner_pri=search.get().priority
    
    search=UploaderBluetoothDongle.objects.filter(address=address)
    if search.count() > 0:
        uploader = True
        uploader_max=search.get().max_conn

    form = form or DongleForm( initial = { 
                                    'address': address, 
                                    'name': name,
                                     'scan': scanner,
                                     'scan_pri': scanner_pri,
                                     'upload': uploader,
                                     'upload_max': uploader_max})

    return render_to_response('op/dongle_form.html',
        { 
            'form':  form,
            'messages': messages,
        }, context_instance=RequestContext(request))

@decorators.staff_member_required
def server_rpc_command(request, command):
    server=rpyc.connect('localhost', 8010)
    func=getattr(server.root, command, None)
    if func is not None:
        rpyc.async(func)()
    return HttpResponseRedirect('/')
    
def grab_file(request, file):
    logger.info("grab_file %s" % file)
    file = CampaignFile.objects.get(file=file).file
    mime = guess_mime(file.name)
    return HttpResponse(file.read(), mimetype=mime[0] )

@decorators.staff_member_required
def stats_restart(request):
    '''
    Delete statistics, we do drop table, not the recommended way but damn
    effective.
    '''
    from django.core import management
    from django.db import connection, models
    from django.core.management.color import no_style
    from django.core.management import sql

    cursor = connection.cursor()
    logger.info("stats restart")

    # this tables are not going to be deleted
    tables = [ 'openproximity_bluetoothdongle',
        'openproximity_campaignfile',
        'openproximity_marketingcampaign',
        'openproximity_remotescannerbluetoothdongle',
        'openproximity_scannerbluetoothdongle',
        'openproximity_uploaderbluetoothdongle',
        'openproximity_generalsetting',
        ]
    model  = models.get_app('openproximity')
    drop = ""
    
    drop_table = sql.sql_delete(model, no_style())
    
    for line in drop_table:
        table_name = line.split()[2].replace('"', '').replace(';','')
    
        if line.startswith('DROP TABLE'):
            # we don't want to loose settings    
            if table_name not in tables:
                drop+="DROP TABLE %s;\n" % table_name
            
            elif line.find('CREATE INDEX') > -1:
                drop += "DROP INDEX %s;\n" % table_name
    try:
        server=rpyc.connect('localhost', 8010)
        server.root.Lock()
        logger.info("database locked")
    except:
        pass

    logger.info("about to drop")
    for line in drop.splitlines():
        try:
            connection.cursor().execute(line)       
        except Exception, err:
            logger.error("%s failed" %line)
            logger.exception(err)

    logger.info("allowing plugins to drop statistic it's tables")

    for plugin in pluginsystem.get_plugins('statistics_reset'):
        try:
            getattr(plugin.module,'statistics_reset')(connection)
        except Exception, err:
            logger.error("plugin failed to reset statistics %s" % plugin)
            logger.exception(err)

    logger.info("calling syncdb")
    management.call_command('syncdb')
    
    try:
        server=rpyc.connect('localhost', 8010)
        server.root.Unlock()
        server.root.restart()
    except:
        pass
    
    logger.info("database unlocked")

    return HttpResponseRedirect('/')
    
def dongle_information(dongle):
    a=dict()
    a['address'] = dongle
                
    search = ScannerBluetoothDongle.objects.filter(address=dongle)
    a['isScanner'] = search.count()>0
    if search.count()>0:
        a['scan_enabled'] = search.get().enabled == True
        a['scan_pri'] = search.get().priority
        
    search = UploaderBluetoothDongle.objects.filter(address=dongle)
    a['isUploader'] = search.count()>0      
    if search.count()>0:
        a['upload_enabled'] = search.get().enabled == True
        a['max_conn'] = search.get().max_conn
    
    return a

def generate_rpc_information():
    # generate rpc information
    rpc = dict()
    rpc['running'] = None
    try:
        server=rpyc.connect('localhost', 8010)
        rpc['running'] = server is not None
        rpc['uploaders'] = server.root.getUploadersCount()
        rpc['scanners'] = server.root.getScannersCount()
        rpc['dongles'] = [ dongle_information(a) for a in 
                server.root.getDongles()]
    except Exception, err:
        rpc['error'] = err

    return rpc

def generate_stats():
    # generate stastics information
    stats = dict()
    try:
        stats['seen'] = dict()
        stats['seen']['total'] = RemoteDevice.objects.count()
        stats['seen']['perdongle'] = list()
        for a in ScannerBluetoothDongle.objects.all():
            b=dict()
            b['address'] = a.address
            b['count'] = RemoteBluetoothDeviceFoundRecord.objects.\
                    filter(dongle=a).count()
            stats['seen']['perdongle'].append( b )
        stats['valid'] = RemoteBluetoothDeviceSDP.objects.count()
    
        accepted = RemoteBluetoothDeviceFilesSuccess.objects.count()
        non_accepted = RemoteBluetoothDeviceFilesRejected.objects.count()
    
        a=RemoteBluetoothDeviceFilesRejected.objects
        for ret in TIMEOUT_RET:
            a=a.exclude(ret_value=ret)
            
        rejected = a.count()
        
        stats['accepted'] = accepted
        stats['rejected'] = rejected
        stats['timeout'] = non_accepted-rejected
        stats['tries'] = accepted+non_accepted

    except Exception, err:
        stats['error'] = err

    return stats

def index(request):
    # generate rpc information
    rpc = generate_rpc_information()
    
    # generate stastics information
    stats = generate_stats()

    version = dict()
    try:
        version['current'] = os.environ['OP2_VERSION'].strip().upper()
    except Exception, err:
        version['error'] = err

    return render_to_response("op/index.html", {
                                               "rpc": rpc,
                                               "camps": getMatchingCampaigns(),
                                               "stats": stats,
                                                "version": version, 
            }, 
            context_instance=RequestContext(request))

def rpc_stats(request):
    stats = generate_stats()
    return HttpResponse(
        simplejson.dumps(stats), 
        content_type="application/json")

def rpc_info(request):
    info = generate_rpc_information()
    return HttpResponse(
        simplejson.dumps(info), 
        content_type="application/json")

def smart_group(group):
    for g in group:
        line=dict()
        for key,val in g.iteritems():
            line[key]=str(val)
        yield line

def rpc_last_seen(request):
    #get a json list of the devices seen in the last 30 minutes
    secs=time.time()-15*60
    start=datetime.fromtimestamp(secs)
    objs=RemoteDevice.objects.filter(
        last_seen__gte=start).order_by('address')

    if objs.count() > 0:
        return HttpResponse(
            simplejson.dumps(
                list(smart_group(
                    objs.values(
                    'address', 
                    'name', 
                    'last_seen', 
                    'devclass')
                    )
                )),
            content_type="application/json")

    return HttpResponse(
        simplejson.dumps({}),
        content_type="application/json")
    
def rpc_device_info(request):
    addr=request.GET.get('address')
    
    out=dict()
    out['accepted'] = RemoteBluetoothDeviceFilesSuccess.objects.\
                        filter(remote__address=addr).count()

    non_accepted = RemoteBluetoothDeviceFilesRejected.objects.\
                        filter(remote__address=addr).count()
    a=RemoteBluetoothDeviceFilesRejected.objects.filter(remote__address=addr)
    for ret in TIMEOUT_RET:
        a=a.exclude(ret_value=ret)
        
    out['rejected'] = a.count()
    out['timeout'] = non_accepted-out['rejected']
    out['tries'] = out['accepted']+non_accepted
    if out['tries'] > 0:
        out['valid'] = RemoteBluetoothDeviceSDP.objects.\
                            filter(remote__address=addr).count()>0
    else:
        out['valid'] = 'N/D'

    return HttpResponse( simplejson.dumps(out), content_type="application/json")

RPC_COMMANDS={
    'stats':        rpc_stats,
    'info':     rpc_info,
    'last-seen':    rpc_last_seen,
    'device-info':  rpc_device_info, 
}

def rpc_command(request, command):
    f = RPC_COMMANDS.get(command, None)
    logger.info("rpc_command %s" % command)
    return f(request) if f else HttpResponse("Non Valid Command")

def last_seen(request):
    return render_to_response("op/last_seen.html", {}, 
        context_instance=RequestContext(request))

