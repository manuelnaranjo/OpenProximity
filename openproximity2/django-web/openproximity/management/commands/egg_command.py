from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.importlib import import_module

class Command(BaseCommand):
    help = "try running a command inside an egg, pass as argument the wanted command"
    
    def handle(self, command="", *args, **kwargs):
	for app in settings.INSTALLED_APPS:
	    try:
	        mod = import_module("%s.management.commands.%s" % (app, command))
	        print "found command"
	    except :
		continue

	    return mod.Command().handle(*args, **kwargs)
	
