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
	import sys
	print 'You need to run syncdb first to init TEST plugin'
	sys.exit(1)
