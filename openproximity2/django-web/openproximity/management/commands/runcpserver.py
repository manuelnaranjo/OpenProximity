#!/usr/bin/env python

from django_cpserver.management.commands.runcpserver import CPSERVER_OPTIONS
from django.conf import settings
from optparse import OptionParser
from configglue.glue import schemaconfigglue


CPSERVER_OPTIONS.update({
    'host': settings.CP_HOST,
    'port': settings.CP_PORT,
    'server_name': settings.CP_SERVER_NAME,
    'threads': settings.CP_THREADS,
    'daemonize': settings.CP_DAEMONIZE,
    'workdir': settings.CP_WORKDIR,
    'pidfile': settings.CP_PIDFILE,
    'server_user': settings.CP_SERVER_USER,
    'server_group': settings.CP_SERVER_GROUP,
    'ssl_certificate': settings.CP_SSL_CERTIFICATE,
    'ssl_private_key': settings.CP_SSL_PRIVATE_KEY,
})

CPSERVER_HELP = r"""
  Run this project in a CherryPy webserver. To do this, CherryPy from
  http://www.cherrypy.org/ is required.
"""


from django_cpserver.management.commands.runcpserver import Command as OCommand

class Command(OCommand):
    def create_parser(self, prog_name, subcommand):
        """
        Add all our SchemaConfigParser's options so they can be shown
        in help messages and such.
        """
        parser = OptionParser(prog=prog_name,
            usage=self.usage(subcommand),
            version=self.get_version(),
            option_list=self.option_list)

        configglue_parser = settings.__CONFIGGLUE_PARSER__
        configglue_parser.setmode("cherrypy")
        op, options, args = schemaconfigglue(configglue_parser, op=parser)
        return op
        
    def usage(self, subcommand):
        return ""
