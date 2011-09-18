#!/usr/bin/env python
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

import sys, os, fnmatch

DJANGO_PATH=os.path.dirname(os.path.realpath(__file__))
OP_PATH=os.path.dirname(DJANGO_PATH)

paths = list()
paths.append(os.path.join(OP_PATH, "libs"))
paths.append(os.path.join(OP_PATH, "django-web"))
paths.append(os.path.join("usr", "lib", "openproximity"))
paths.append(os.path.expanduser(os.path.join('~', '.openproximity')))

def find_all_eggs(parent):
  for par, subdirs, files in os.walk(parent, followlinks=True):
    for f in fnmatch.filter(files, '*.egg'):
      yield os.path.join(par, par, f)

for p in list(paths):
  paths.extend(find_all_eggs(p))

sys.path = paths + sys.path

try:
    from openproximity import version
except:
    version = 'ND'
os.environ['OP2_VERSION'] = version
