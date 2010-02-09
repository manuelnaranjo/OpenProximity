from django import template
from django.conf import settings
from net.aircable.openproximity.pluginsystem import pluginsystem

SET = settings.OPENPROXIMITY.getAllSettings()

register=template.Library()

def do_settings(parser, token):
    return SettingsNode()

class SettingsNode(template.Node):
    def render(self, context):
	context['settings'] = SET
	return ''

register.tag('settings', do_settings)

def do_plugins(parser, token):
    return PluginsNode()

class PluginsNode(template.Node):
    def render(self, context):
	context['plugins'] = pluginsystem.get_plugins('urls')
	return ''
register.tag('plugins', do_plugins)

@register.simple_tag
def createNavButton(ref, rid, text, style):
    return '''<a class="nav_button" title="%s" id="%s" href="%s">
	<div style="%s" >%s</div></a>''' % (text, rid, ref, style, text)

