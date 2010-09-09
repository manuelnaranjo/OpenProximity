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

# Camera Plugin definition
name='BT Camera plugin'		# friendly name
enabled=True			# disable me please
django=True			# expose me as a django enabled plugin

post_environ=False		# no post environ

TEMPLATE_DIRS='templates'	# static media I give to django
LOCALE_PATHS='locale'
django_app=True			# we provide an application so we can
				# define models

statistics_reset=True
urls=( 'camera', 'urls' )	# urls I give to django

serverxr=True			# we have our own rpc client
serverxr_type='camera'
serverxr_manager='CameraManager'

rpc=True		# provide rpc handle
rpc_register = True	# sensorsdk generic client will register with us
found_action = True	# we will handle the found_action signal
