# -*- coding: utf-8 -*-
# OpenProximity2.0 is a proximity marketing OpenSource system.
# Copyright (C) 2010,2009,2008 Naranjo Manuel Francisco <manuel@aircable.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# this file will be called by settings and others, before django.conf.settings
# is available

import sys, os, setpaths
__PATH=os.path.dirname(os.path.abspath(__file__))
__ROOT=os.path.dirname(__PATH)
__LIBS=os.path.join(__ROOT, 'libs')

from configglue.parser import SchemaConfigParser
from django_configglue.utils import update_settings
from functools import partial
import schema

OPENPROXIMITY_CONFIG_FILE=os.environ.get('OPENPROXIMITY_CONFIG_FILE', "/etc/openproximity2.conf")

# parse config files
parser=SchemaConfigParser(schema.OpenProximitySchema())
parser._interpolate = partial(schema._interpolate, parser)
parser.read([ os.path.join(__PATH, 'default.cfg'),
        os.path.join(__PATH, 'django.cfg'),
        os.path.join(__PATH, 'cherrypy.cfg'),
        os.path.join(__PATH, 'rpyc.cfg'),
        os.path.join(__PATH, 'debug.cfg'),
        OPENPROXIMITY_CONFIG_FILE])
update_settings(parser, locals())

# fix timeout in DATABASE_OPTIONS
if 'timeout' in locals()['DATABASE_OPTIONS']:
    locals()['DATABASE_OPTIONS']['timeout'] = \
        float(locals()['DATABASE_OPTIONS']['timeout'])

locals()['DEBUG_DISABLES']=locals()['DEBUG_DISABLES'].split(',')

# keep a reference to the parser
__CONFIGGLUE_PARSER__ = parser
