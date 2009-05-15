from django import template
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.template.context import Context
from django.utils.translation import ugettext as _


register = template.Library()

@register.simple_tag
def remote_name(adapter, address):
    #return "%s %s" % (adapter, address)
    return adapter.GetRemoteName(address)
    
@register.simple_tag
def remote_trust(adapter, address):
    ret = adapter.HasBonding(address)!=0
    if ret:
	return _("Yes")
    else:
	return _("No")

@register.simple_tag
def remote_lastseen(adapter, address):
    #return "%s %s" % (adapter, address)
    return adapter.LastSeen(address)
