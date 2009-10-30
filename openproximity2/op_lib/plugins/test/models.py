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




# test plugin
# defines new clases for db integration

from openproximity.models import DeviceRecord
from django.db import models
from django.utils.translation import ugettext as _

class ExtraRecordInformation(models.Model):
    '''Sample model class that just adds a tag to a device record in order to avoid 
	problems with the database schema, we suggest that you add references to 
	original OP2 classes instead of inheriting from those
    '''
    record = models.ForeignKey(DeviceRecord)
    tag = models.CharField(max_length=100)

try:
    ''' test method to tell if DB needs to be updated '''
    ExtraRecordInformation.objects.all().count()
except Exception, err:
    if str(err).lower().find('table not') > -1:
	print err
	print 'You need to run syncdb first to init TEST plugin'
