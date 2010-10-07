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
from django.db import models
from pickle import loads, dumps

class PickledField(models.CharField):
    '''
	A simple class that can be used to store settings in django db
    '''
    __metaclass__ = models.SubfieldBase
    
    def to_python(self, value):
	if type(value) is unicode:
	    value=str(value)
	try:
	    return loads(value)
	except:
	    return value
	    
    def get_db_prep_value(self, value):
	if type(value) is unicode:
	    value=str(value)
	try:
	    if type(value) is str:
		value=eval(value)
	    if type(value) is not str:
		value = dumps(value)
	except:
	    pass
	return ''.join(value)
