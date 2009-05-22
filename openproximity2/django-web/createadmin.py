#!/usr/bin/env python
from django.core.management import setup_environ
from django.core.management import call_command

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    setup_environ(settings)
    call_command("createsuperuser", noinput=True, username="admin", email="foo@foo.com")
    from django.contrib.auth.models import User
    user = User.objects.get(username='admin')
    user.set_password("aircable")
    user.save()
