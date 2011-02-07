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

from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views import decorators
from methods import getSetting, setSetting
from django.utils.translation import ugettext as _
from models import UploadRecord
from subprocess import Popen, PIPE, call
import tempfile, os
import forms

def getSettings(request):
    out = {
	'enabled': getSetting('enabled', True)
    }
    for key in ['server', 'hash_id' ]:
	out[key]=getSetting(key, None)

    cron=""
    for key in ['cron_minute', 'cron_hour', 'cron_dom', 'cron_month', 'cron_dow' ]:
	cron="%s %s" % (cron, getSetting(key, 'INV'))
    out['cron'] = cron
    if request.user.is_staff:
	out['password']=getSetting('password', None)
    elif getSetting('password', None):
	out['password']=_("Hidden")
    return out

def dosetup(**kwargs):
    if 'enabled' not in kwargs:
	kwargs['enabled'] = False

    kwargs['server']=kwargs['server'][:-1] # take out extra /
    for set in ['hash_id', 'server', 'password', 'enabled',
		'cron_minute', 'cron_hour', 'cron_dom', 'cron_month', 'cron_dow']:
	setSetting(set, kwargs[set])

    old_crontab=Popen(['crontab', '-l'], stdout=PIPE).communicate()[0]
    print old_crontab

    filename = tempfile.mkstemp('crontab')[1]
    new_crontab=file(filename, 'w')
    for line in old_crontab.splitlines():
	if line.find('pushrecords')==-1:
	    new_crontab.write('%s\n' % line)

    if kwargs['enabled']:
	line = '%(cron_minute)s %(cron_hour)s %(cron_dom)s %(cron_month)s %(cron_dow)s' % kwargs
	line = '%s cd /opt/openproximity2; /bin/bash manager.sh egg_command pushrecords >> /tmp/pushrecords.log' % line
	new_crontab.write('%s\n' % line)
    new_crontab.close()

    call(['crontab', filename])
    print Popen(['crontab', '-l'], stdout=PIPE).communicate()[0]
    os.unlink(filename)


@decorators.staff_member_required
def setup(request):
    def getSettingsSetup():
	out = {
	    'enabled': getSetting('enabled', True)
	}
	for key in ['server', 'hash_id' ]:
	    out[key]=getSetting(key, None)

	out['cron_minute']=getSetting(key, '*/15')
	for key in ['cron_minute', 'cron_hour', 'cron_dom', 'cron_month', 'cron_dow']:
	    out[key]=getSetting(key, '*')
	out['password']=getSetting('password', None)
	return out

    if request.method=='POST':
	form=forms.SetupForm(request.POST)
	if form.is_valid():
	    print form.cleaned_data
	    dosetup(**form.cleaned_data)
	    return HttpResponseRedirect(reverse("agent2"))
    else:
        form=forms.SetupForm(initial=getSettingsSetup())
    return render_to_response("agent2/setup.html",{ 
	'form': form ,
    },context_instance=RequestContext(request))

def index(request):
    return render_to_response("agent2/index.html",{ 
	'agent2_settings': getSettings(request),
	'records': UploadRecord.objects.all().order_by("-time")[0:10]
    }, context_instance=RequestContext(request))
