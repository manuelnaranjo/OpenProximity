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
from net.aircable.openproximity.signals import scanner as signals
from openproximity.models import *

from rpyc import async
from pickle import loads, dumps

def get_uploader(services):
    for i in services:
	if getattr(i, 'uploader', None) is not None:
	    return i
    return None

def do_upload(uploader, files, remote):
    print "About to call upload"
    uploader.upload(dumps(files), remote)
    print "upload called async"
