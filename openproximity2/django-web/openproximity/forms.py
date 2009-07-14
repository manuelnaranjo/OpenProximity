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
    
    position_x = forms.DecimalField(required=False)
    position_y = forms.DecimalField(required=False)

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
	    # if you're reading this that means you can read some code
	    # and you might want to figure out how to use OP2 with non aircable
	    # dongles. Well I'm not going to tell you to remove this lines
	    # I'm only going to tell you that this are not the only. You should
	    # check code under op2/serverXR too :D
	    # MN
	    raise forms.ValidationError("Only AIRcable dongles are allowed to upload")
	return self.cleaned_data['upload'] 

class CampaignForm(forms.ModelForm):
    friendly_name = forms.CharField(max_length=100) # dont' want a multi line field here
    
    class Meta:
	model = MarketingCampaign
	#fields = ('friendly_name',)
