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

from net.aircable.utils import logger, logmain

if __name__ == '__main__':
    logmain("manage")
    
from django.core.management import execute_manager, setup_environ
try:
    import settings # Assumed to be in the same directory.
    setup_environ(settings)
except ImportError, e:
    import sys, traceback
    logger.error("Error: Can't find the file 'settings.py' in the directory "
            "containing %r. It appears you've customized things.\nYou'll have "
            "to run django-admin.py, passing it your settings module.\n(If the "
            "file settings.py does indeed exist, it's causing an ImportError "
            "somehow.)\n" % __file__)
    logger.exception(e)
    sys.exit(1)

from net.aircable.openproximity.pluginsystem import pluginsystem
pluginsystem.post_environ()

if __name__ == "__main__":
    execute_manager(settings)
    
