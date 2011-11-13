#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading, time, traceback, sys, os
from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option, OptionParser
from configglue.glue import schemaconfigglue

CLIENT_OPTIONS = {
    'host': settings.CLIENT_HOST,
    'port': settings.CLIENT_PORT,
    'mode': settings.CLIENT_MODE,
    'daemonize': settings.CLIENT_DAEMONIZE,
    'pidfile': settings.CLIENT_PIDFILE,
}

class Command(BaseCommand):
    help = "RPyC Client for OpenProximity."

    def handle(self, *args, **options):
        runclient(args)

    def usage(self, subcommand):
        return self.help

    def create_parser(self, prog_name, subcommand):
        """
        Add all our SchemaConfigParser's options so they can be shown
        in help messages and such.
        """
        parser = OptionParser(prog=prog_name,
            usage=self.usage(subcommand),
            version=self.get_version(),
            option_list=self.option_list)

        cg_parser = settings.__CONFIGGLUE_PARSER__
        cg_parser.setmode("client")
        op, options, args = schemaconfigglue(cg_parser, op=parser)
        return op

def runclient(argset=[], **kwargs):
    # Get the options
    options = CLIENT_OPTIONS.copy()
    options.update(kwargs)

    from net.aircable.utils import getLogger
    logger = getLogger(__name__)

    if options['daemonize']:
        if not options['pidfile']:
            options['pidfile'] = '/var/run/openproximity_client_%s_%s.pid' % ( \
                options['mode'], options['port'] )

        logger.info("storing pid file in %s" % options['pidfile'])
        from django.utils.daemonize import become_daemon
        
        logger.info("daemonizing")
        become_daemon()
        logger.info("daemonized")

        fp = open(options['pidfile'], 'w')
        fp.write("%d\n" % os.getpid())
        fp.close()

    # Start the rpc server
    logger.debug('starting client with options %s' % options)
    mode = options['mode']
    host = options['host']
    port = int(options['port'])
    valid_modes=['scanner', 'uploader', 'pairing']
    from net.aircable.openproximity.pluginsystem import pluginsystem
    valid_modes.extend([ \
            i.provides['serverxr_type'] for i in \
                pluginsystem.get_plugins('serverxr')])
    if mode not in valid_modes:
        print "not a valid mode, use any of", valid_modes
        sys.exit(1)
    from rpc_clients import manager
    manager.run(host, port, mode)

if __name__ == '__main__':
    runclient(sys.argv[1:])
