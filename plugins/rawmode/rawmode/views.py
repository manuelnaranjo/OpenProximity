# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse

from openproximity.models import RemoteDevice
from lxml import etree

from PyOBEX2 import common
from PyOBEX2.asyncsocket import init
from PyOBEX2.asyncoop import Client

import time, pprint

CHANNEL_XPATH=etree.XPath("/record/attribute[@id='0x0004']/sequence/sequence/uuid[@value='0x0003']/../uint8/@value")
UUID={
    'opp':'00001105-0000-1000-8000-00805f9b34fb',
    'ftp':'00001106-0000-1000-8000-00805f9b34fb'
}

def XmlToDict(content):
  def __todict_from_keys(block):
    keys = block.keys()
    out=dict()
    for k in keys:
      out[k]=block.get(k)
    return out

  def __todict(block):
    out = dict()
    for children in list(block):
      tag = "%s: %s" % (children.tag, __todict_from_keys(children))
      if len(list(children)) > 0:
	out[tag] = __todict(children)
      else:
	out[tag] = children
    return out
  tree = etree.fromstring(str(content))
  return __todict(tree)

def GetChannelFromXML(services):
  for key in services.keys():
    root=etree.XML(str(services[key]))
    res=CHANNEL_XPATH(root)
    if len(res)>0:
      return str(int(res[0], 16))

def GenerateRemoteDeviceChoices():
    for device in RemoteDevice.objects.all():
	yield ( device.address, '%s: %s' % (device.address, device.name) )

def ChannelChoices():
    yield ('resolve', 'Resolve SDP')

    for i in range(0, 100):
	yield( str(i), 'Force: %s' % i)

class RawModeForm(forms.Form):
    remote_device = forms.ChoiceField(
	    choices=GenerateRemoteDeviceChoices(),
	    required=True,
	    label=_("Remote Device"),
	    help_text=_("Select the device to upload a file too")
    )

    service = forms.ChoiceField(
	    choices=(
		('ftp', 'OBEX FTP (requires pairing)'),
		('opp', 'OBEX Object Push (may require pairing)'),
	    ),
	    required=True,
	    initial='opp'
    )

    channel = forms.ChoiceField(
	    choices=ChannelChoices(),
	    required=True,
	    initial='resolve'
    )

    file_ = forms.FileField(
	required=True,
	help_text=_("File to upload"),
	label=_("File"),
    )

def resolve_channel(service, remote_device):
    import dbus, re

    yield "Connecting to dbus..."
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.bluez.Manager")
    adapter = dbus.Interface(bus.get_object("org.bluez", manager.DefaultAdapter()),
							"org.bluez.Adapter")

    yield "Creating Device..."
    try:
	device = adapter.CreateDevice(remote_device)
	yield "Created %s" % device
    except:
	device = adapter.FindDevice(remote_device)
	yield "All ready created %s" % device

    yield "Resolving services..."

    device = dbus.Interface(bus.get_object("org.bluez", device),
					    "org.bluez.Device")

    services = device.DiscoverServices("");
    for key in services.keys():
	p = re.compile(">.*?<")
	xml = p.sub("><", services[key].replace("\n", ""))
	yield "[ 0x%5x ]" % (key)
	yield pprint.pformat(XmlToDict(xml))
	yield ""

    properties = device.GetProperties()
    if UUID[service] not in properties['UUIDs']:
	yield "Service not provided"
	raise StopIteration()

    yield "Provides service"
    services = device.DiscoverServices(UUID[service])
    yield GetChannelFromXML(services)

def doUpload(file_, service, remote_device, channel, *args, **kwargs):
    yield "Connecting\n\r"
    def callback(client, response=None):
      print "callback ", args, kwargs
      if client.state == common.CONNECTING_RFCOMM:
	print "connected rfcomm\r\n"
	client.connect_obex()
      elif client.state == common.CONNECTING_OBEX:
	print "connected obex\r\n"
	client.put(file_.name, file_.read())
      elif client.state == common.PUT:
	print "uploaded completed"
	loop.quit()
      else:
	print "something completed %s %s %s" % (common.STATES[client.state], args, kwargs)

    def error(client, error):
	yield "error %s %s" % client.state, error
	client.invalid=True
	loop.quit()

    import sys, gobject
    loop=gobject.MainLoop()
    client = Client(loop=loop)
    yield "connecting rfcomm\n\r"
    client.connect_rfcomm(remote_device, channel, callback, error)
    init()
    if not getattr(client, 'invalid', False):
      yield "running loop\n\r"
      loop.run()
    yield "Success: %s\n\r" % not getattr(client, 'invalid', False)
    yield "all done\n\r"

def HandleUpload(file_=None, service='opp', remote_device=None, channel='resolve'):
    yield "<html><body><pre>"

    if not channel.isdigit():
	yield "resolving channel...\r\n"
	try:
	  for i in resolve_channel(service, remote_device):
	    if type(i)==str and i.isdigit():
	      channel=int(i)
	    else:
	      yield "%s\r\n" % i
	except Exception, err:
	  yield err

    if type(channel)==int:
      yield "Using service %s to %s:%s....\r\n" % (service, remote_device, channel)
      try:
	for repl in doUpload(file_, service, remote_device, channel):
	  yield repl
      except Exception, err:
	  print err

    yield "done\r\n"
    yield "</pre></body></html>"

def index(request, arg):
    form = None
    if request.method == 'POST':
	form = RawModeForm(request.POST, request.FILES)
	if form.is_valid():
	    return HttpResponse(HandleUpload(**form.cleaned_data))
    else:
	form = RawModeForm()
    return render_to_response('rawmode/index.html',
        {
         'form': form,
        })
