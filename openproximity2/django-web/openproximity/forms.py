from django import forms
from re import compile
from models import MarketingCampaign

AIRCABLE_MAC=['00:50:C2', '00:25:BF']
ADDRESS_MAC=compile("([0-9A-F]{2}\:){5}([0-9A-F]{2})")

def isAIRcable(address):
    return address[:8].upper() in AIRCABLE_MAC

class DongleForm(forms.Form):
    address = forms.CharField()
    name = forms.CharField(max_length=20)
    scan = forms.BooleanField(required=False)
    scan_pri = forms.IntegerField(required=False)
    upload = forms.BooleanField(required=False)
    upload_max = forms.IntegerField(required=False)

    def clean_address(self):
	address = self.cleaned_data['address']
	if ADDRESS_MAC.match(address):
	    self.isAIRcable=isAIRcable(address)
	    return address
	raise forms.ValidationError("Not a Bluetooth Address")

    def clean_upload(self):
	isAIR = getattr(self, 'isAIRcable', None)
	upload = self.cleaned_data['upload']
	if not isAIR and upload:
	    raise forms.ValidationError("Only AIRcable dongles are allowed to upload")
	return self.cleaned_data['upload'] 

class CampaignForm(forms.ModelForm):
    friendly_name = forms.CharField(max_length=100) # dont' want a multi line field here
    
    class Meta:
	model = MarketingCampaign
	#fields = ('friendly_name',)
