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

from configglue.pyschema import SchemaConfigParser
from django_configglue.utils import update_settings
from functools import partial
import schema, os

OPENPROXIMITY_CONFIG_FILE=os.environ.get('OPENPROXIMITY_CONFIG_FILE', "/etc/openproximity2.conf")

# parse config files
parser=SchemaConfigParser(schema.OpenProximitySchema())
parser._interpolate = partial(schema._interpolate, parser)
parser.read(['default.cfg', 'django.cfg', 'cherrypy.cfg', OPENPROXIMITY_CONFIG_FILE])
update_settings(parser, locals())

# fix timeout in DATABASE_OPTIONS
if 'timeout' in locals()['DATABASE_OPTIONS']:
    locals()['DATABASE_OPTIONS']['timeout'] = float(locals()['DATABASE_OPTIONS']['timeout'])

# keep a reference to the parser
__CONFIGGLUE_PARSER__ = parser

# keep loading modules
from net.aircable.utils import logger
from net.aircable.openproximity.pluginsystem import pluginsystem

logger.info("starting up plugins")
pluginsystem.find_plugins(locals()['OP2_PLUGINS'])
for plugin in pluginsystem.get_plugins('django'):
    if plugin.provides.get('TEMPLATE_DIRS', None) is not None :
        TEMPLATE_DIRS += ( os.path.join(plugin.path, plugin.provides['TEMPLATE_DIRS']), )
    if plugin.provides.get('LOCALE_PATHS', None) is not None:
        LOCALE_PATHS += ( os.path.join(plugin.path, plugin.provides['LOCALE_PATHS']), )
    if plugin.provides.get('django_app', False):
        INSTALLED_APPS += (plugin.name,)

logger.info("starting up plugin providers")
for plugin in pluginsystem.get_plugins('plugin_provider'):
    for plug in pluginsystem.get_plugins(plugin.provides['plugin_provider_name']):
        INSTALLED_APPS += (plug.name, )

logger.info("plugin system initied")
logger.info("settings.py loaded")

def __get_match_dongle(options, address):
    def __parse(option, typ=int):
	if len(option.strip()) == 0:
	    return None
	return typ(option)

    address = address.lower().strip()
    for rang, val, enable, name in options:
	rang = rang.lower().strip()

	if address.startswith(rang):
	    out = { 'enable': __parse(enable, bool), 'value': __parse(val), 'name': __parse(name, str) }
	    return out

GETSCANNERDONGLE=partial(__get_match_dongle, locals()['OP2_SCANNERS'])
GETUPLOADERDONGLE=partial(__get_match_dongle, locals()['OP2_UPLOADERS'])
