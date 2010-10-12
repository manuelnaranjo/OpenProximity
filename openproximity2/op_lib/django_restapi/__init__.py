from django_restapi.resource import Resource, ResourceBase
from django_restapi.model_resource import Collection, Entry
from django_restapi.receiver import *
from django_restapi.responder import *
from django_restapi.authentication import *
from django_restapi.sites import site, RestSite

from django.utils.importlib import import_module


# A flag to tell us if autodiscover is running.  autodiscover will set this to
# True while running, and False when it finishes.
LOADING_REST = False

def autodiscover():
    """
    Auto-discover INSTALLED_APPS rest.py modules and fail silently when
    not present. This forces an import on them to register any rest bits they
    may want.
    """
    # Bail out if autodiscover didn't finish loading from a previous call so
    # that we avoid running autodiscover again when the URLconf is loaded by
    # the exception handler to resolve the handler500 view.  This prevents an
    # rest.py module with errors from re-registering models and raising a
    # spurious AlreadyRegistered exception (see #8245).
    global LOADING_REST
    if LOADING_REST:
        return
    LOADING_REST = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for an rest.py inside that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for rest.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # need to roll their own rest registration.
        try:
            app_path = import_module(app).__path__
        except AttributeError, err:
            continue

        # Step 2: use imp.find_module to find the app's rest.py. For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its rest.py doesn't exist
        try:
            imp.find_module('rest', app_path)
        except ImportError, err:
            continue

        # Step 3: import the app's rest file. If this has errors we want them
        # to bubble up.
        import_module("%s.rest" % app)
    # autodiscover was successful, reset loading flag.
    LOADING_REST = False
