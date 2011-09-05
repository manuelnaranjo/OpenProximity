#    OpenProximity2.0 is a proximity marketing OpenSource system.
#    Copyright (C) 2010,2009 Naranjo Manuel Francisco <manuel@aircable.net>
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


from django import template
from django.conf import settings
from net.aircable.openproximity.pluginsystem import pluginsystem

register=template.Library()

def do_settings(parser, token):
    return SettingsNode()

class SettingsNode(template.Node):
    def render(self, context):
        context['settings'] = {
            'logo': settings.OP2_LOGO,
            'debug': settings.OP2_DEBUG,
            'translate': settings.OP2_TRANSLATE,
            'twitter': settings.OP2_TWITTER,
        }
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
def createNavButton(ref, rid, text, style=None):
    return '''<div class="nav_button button" 
            id="%(id)s" onclick="%(href)s">%(text)s</div>''' % { 
                'id': rid, 'href': ref, 'text': text, 'style': style or ''}
