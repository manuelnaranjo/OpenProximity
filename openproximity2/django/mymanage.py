#!/usr/bin/env python
from django.core.management import setup_environ, ManagementUtility

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)
    
def my_func():
    try:
	from openproximity.models import DeviceRecord
	print DeviceRecord.objects.all()
    except:
	sys.exit(0)

if __name__ == "__main__":
    import sys
    setup_environ(settings)
    utility = ManagementUtility(sys.argv)

    import threading, time
    threading.Thread(target=my_func).start()
    print threading.activeCount()
    utility.execute()
