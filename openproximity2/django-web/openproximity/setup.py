# -*- coding: utf-8 -*-
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

from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.views.generic import list_detail
from django.utils.translation import ugettext as _
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

from django import forms
from timezones.forms import TimeZoneField
from timezones import zones
import pytz

def mycmp(x, y):
    a=int(x[4:9])
    b=int(y[4:9])
    return cmp(a,b)


class MyTimeZoneField(TimeZoneField):
    def __init__(self, *args, **kwargs):
        a=dict(zones.PRETTY_TIMEZONE_CHOICES).values()
        a.sort(mycmp)
        tz=tuple(zip(a, a))
        kwargs['choices'] = tz
        super(MyTimeZoneField, self).__init__(*args,**kwargs)
    
    def clean(self, value, *args, **kwargs):
        value=value[11:]
        try:
            return pytz.timezone(value)
        except:
            raise forms.ValidationError(_("Invalid option"))

class UserForm(forms.Form):
    username = forms.CharField(max_length=100, label=_("Username:"))
    password1 = forms.CharField(
                    label=_("Password:"), 
                    max_length=100,
                    widget=forms.widgets.PasswordInput)
    password2 = forms.CharField(
                    label=_("Type Again"), 
                    max_length=100,
                    widget=forms.widgets.PasswordInput)
    email = forms.EmailField()
    time_zone = MyTimeZoneField()

    def clean(self):
        cleaned_data = self.cleaned_data
        pass1 = cleaned_data.get("password1", None)
        pass2 = cleaned_data.get("password2", None)
        if pass1 != pass2:
            self._errors["password2"]=_("Passwords don't match")
            if "password2" in cleaned_data:
                del cleaned_data["password2"]

        return cleaned_data

def db_ready():
    try:
        from models import BluetoothDongle, UserProfile
        BluetoothDongle.objects.count()
        if UserProfile.objects.count() > 0:
            return True
    except:
        pass
    return False

def CreateDB():
    from django.core import management
    import rpyc
    os.system('mkdir -p %s' % settings.AIRCABLE_PATH)
    try:
        server=rpyc.connect('localhost', 8010)
        server.root.Lock()
        logger.info("database locked")
    except:
        pass

    management.call_command("syncdb", interactive=False)
    
    management.call_command("migrate", all_apps=True, interactive=False)
    
    try:
        server=rpyc.connect('localhost', 8010)
        server.root.Unlock()
        server.root.restart()
    except:
        pass


def CreateAdmin(username, password, email, time_zone):
    from django.contrib.auth.models import User
    if len(User.objects.filter(username=username))>0:
        admin = User.objects.get(username=username)
    else:
        admin = User.objects.create_superuser(username, email, password)
        admin.save()
    profile = admin.userprofile_set.create()
    profile.timezone = time_zone
    profile.save()

def CreateSecretKey():
    from random import choice, seed
    seed()
    key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    A=open(settings.OPENPROXIMITY_CONFIG_FILE, 'a+')
    A.write('[django]\n')
    A.write('secret_key=%s\n' % key)
    A.write('\n')
    A.close()

def index(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            CreateSecretKey()
            CreateDB()
            print form.cleaned_data
            CreateAdmin( 
                form.cleaned_data['username'],
                form.cleaned_data['password1'],
                form.cleaned_data['email'],
                form.cleaned_data['time_zone']
            )
            return render_to_response("op/setup.html", { "done": True })
    else:
        form = UserForm()

    version = dict()
    try:
        version['current'] = os.environ['OP2_VERSION'].strip().upper()
    except Exception, err:
        version['error'] = err

    return render_to_response("op/setup.html", {
            "db_ready": db_ready(),
            "user": form,
            "version": version, 
        }, context_instance=RequestContext(request))
    
 
