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
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import ugettext as _

SET = settings.OPENPROXIMITY.getAllSettings()
AGENT = settings.OPENPROXIMITY.getDict('agent/', {
    'server': "http://www.openproximity.com/stats",
    'customer': None,
    'site': None,
    'interval': 15,
    'enabled': True}
)

class SetupForm(forms.Form):
    server = forms.CharField(max_length=200, initial=AGENT['server'])
    customer_id = forms.CharField(max_length=30, required=False, initial=AGENT.get('customer', ''))
    site_id = forms.CharField(max_length=30, required=False, initial=AGENT.get('site',''))
    enabled = forms.BooleanField(initial=AGENT.get('enabled',True))
    interval = forms.IntegerField(required=False, initial=AGENT.get('interval', 15))

    def clean(self):
	cleaned_data = self.cleaned_data
	site = cleaned_data.get('site_id')
	customer_id = cleaned_data.get('customer_id')
	if site and not customer_id:
	    raise forms.ValidationError(_('You need to provide customer_id if you provide site_id'))
	
	return cleaned_data

@login_required
def configure(request):
    messages = None
    if request.method == 'POST':
	form = SetupForm(request.POST)
	if form.is_valid():
	    server = form.cleaned_data['server']
	    customer = form.cleaned_data['customer_id']
	    site = form.cleaned_data['site_id']
	    enabled = form.cleaned_data['enabled']
	    interval = form.cleaned_data['interval']
	    print server, customer, site, enabled, interval
	    messages = _("Settings Saved")
    else:
	form = SetupForm()
    
    return render_to_response('agent/setup.html', 
	{
	    'form': form,
	    'settings': SET,
	    'messages': messages
	}
    )

def index(request, arg):
    return HttpResponse("Hello World, I'm test plugin")
