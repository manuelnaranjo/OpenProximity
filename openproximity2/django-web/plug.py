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

import os, sys
from net.aircable.openproximity.pluginsystem import pluginsystem

from net.aircable.utils import getLogger
logger = getLogger(__name__)

TEMPLATE_DIRS=()
LOCALE_PATHS=()
INSTALLED_APPS=()

logger.info("starting up plugins")
for plugin in pluginsystem.get_plugins('django'):
    if plugin.provides.get('TEMPLATE_DIRS', None) is not None :
        TEMPLATE_DIRS += ( 
            os.path.join(plugin.path, plugin.provides['TEMPLATE_DIRS']), )
    if plugin.provides.get('LOCALE_PATHS', None) is not None:
        LOCALE_PATHS+=( 
            os.path.join(plugin.path, plugin.provides['LOCALE_PATHS']), )
    if plugin.provides.get('django', False):
        INSTALLED_APPS+=( plugin.name, )

logger.info("starting up plugin providers")
for plugin in pluginsystem.get_plugins('plugin_provider'):
    for plug in pluginsystem.get_plugins(
            plugin.provides['plugin_provider_name']):
        INSTALLED_APPS+=( plug.name, )

logger.info("plugin system initied")
logger.info("settings.py loaded")
