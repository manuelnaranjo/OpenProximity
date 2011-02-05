from django import forms
from django.utils.translation import ugettext as _
import models
import methods

class SetupForm(forms.Form):
    server = forms.URLField(max_length=200,
	help_text=_("Server to connect to"),
	verify_exists=True)
    enabled = forms.BooleanField(initial=True, required=False,
	help_text=_("Do you want to commit your records?"))
    hash_id = forms.CharField(max_length=200,
	help_text=_("Site hash_id generated from main server"))
    password = forms.CharField(max_length=200,
	help_text=_("Site password generated from main server"))
    cron_minute = forms.CharField(initial='*/15',
	help_text=_("Crontab option for minutes"))
    cron_hour = forms.CharField(initial='*',
	help_text=_("Crontab option for hours"))
    cron_dom = forms.CharField(initial='*',
	help_text=_("Crontab option for day of month"))
    cron_month = forms.CharField(initial='*',
	help_text=_("Crontab option for month"))
    cron_dow = forms.CharField(initial='*',
	help_text=_("Crontab option for day of week"))


    def clean(self):
	for key in ['hash_id', 'password']:
	    self.cleaned_data[key] = self.cleaned_data[key].strip()
	r=methods.test_connection(**self.cleaned_data)
	if not r:
	    raise forms.ValidationError(_("Credentials are not invalid"))
	return self.cleaned_data
