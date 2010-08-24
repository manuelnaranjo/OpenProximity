from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.utils import simplejson

import subprocess, os, signal, time, sys


PID_FILE = os.path.join('/', 'tmp', 'remotecontrol.pid')
LOG_FILE = os.path.join('/', 'tmp', 'remotecontrol.log')

def getrunning(request):
    return HttpResponse(
	simplejson.dumps(isRunning()),
	content_type='application/json'
    )

def getlog(request):
    log = {}
    if os.path.isfile(LOG_FILE):
	log['log'] = open(LOG_FILE).read()

    return HttpResponse(
	    simplejson.dumps(log), 
	    content_type='applicaction/json'
	)

def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
	os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

class HostForm(forms.Form):
    host_address = forms.CharField(label=_("Host Address"))
    host_port = forms.IntegerField(label=_("Host Port"))
    username = forms.CharField(label=_("Login User"), required=False)

class RedirectForm(forms.Form):
    local_port = forms.IntegerField(label=_("Local Port"))
    local_host = forms.CharField(label=_("Local Host"), initial="127.0.0.1")
    remote_port = forms.IntegerField(label=_("Remote Port"), initial="0")

RedirectFormSet = forms.formsets.formset_factory(RedirectForm, extra=3)

def start_and_connect(host, redirects):
    def gen_args_list(host, redir):
	yield 'remotecontrolclient'

	yield '-L'
	yield LOG_FILE

	if len (host.get('username', '').strip()) > 0:
	    yield '-l'
	    yield host.get('username').strip()

	if host.get('host_port'):
	    yield '-p'
	    yield str(host.get('host_port'))

	for r in redir:
	    if len(r) > 0:
		yield '-R'
		yield '%s:%s:%s' % ( 
			r['remote_port'], 
			r['local_host'],
			r['local_port'])

	yield host.get('host_address')

    args = list(gen_args_list(host, redirects))
    p=os.fork()
    if p != 0:
	time.sleep(2)
	os.wait() # wait for child to end
    else:
	os.chdir('/')
	os.setsid()
	os.umask(0)

	p = os.fork()
	if p != 0:
	    b=open(PID_FILE, 'w')
	    b.write(str(p))
	    b.close()
	    sys.exit(0)
	else:
	    os.execvp('remotecontrolclient', args)

def stop():
    if not os.path.isfile(PID_FILE):
	return False

    try:
	pid = int(open(PID_FILE).read().strip())
	cmdline = open(os.path.join('/', 'proc', str(pid), 'cmdline')).read()
    except:
	return False
	
    if 'remotecontrolclient' not in cmdline:
	return False

    os.kill(pid, 15)
    os.remove(PID_FILE)

def doStop(request):
    stop()
    return HttpResponse(
	    simplejson.dumps(True), 
	    content_type='application/json'
	)

def isRunning():
    if not os.path.isfile(PID_FILE):
	return False
    try:
	pid = int(open(PID_FILE).read().strip())
	cmdline = open(os.path.join('/', 'proc', str(pid), 'cmdline')).read()
    except:
	return False
    
    return 'remotecontrolclient' in cmdline

def index(request):
    if request.method == 'POST':
	host_form = HostForm(request.POST, request.FILES, prefix="host")
	redirect_form = RedirectFormSet(request.POST, request.FILES, 
							    prefix="redirect")
	if host_form.is_valid() and redirect_form.is_valid():
	    start_and_connect( host_form.cleaned_data, 
				redirect_form.cleaned_data)
    else:
	host_form = HostForm(prefix="host")
	redirect_form = RedirectFormSet(prefix="redirect")

    log = ''
    if os.path.isfile(LOG_FILE):
	log = open(LOG_FILE).read()
    return render_to_response(
	'remotesupport/index.html',
	{
	    'running': isRunning(),
	    'host_form': host_form,
	    'redirect_form': redirect_form,
	}
    )
