#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading, time, traceback, sys
from openproximity.rpc import server
from rpyc import Service, async
from rpyc.utils.server import ThreadedServer, ForkingServer
from django.core.management.base import BaseCommand
from django.conf import settings

SERVER_OPTIONS = {
    'host': settings.RPC_HOST,
    'port': settings.RPC_PORT,
    'autoregister': settings.RPC_AUTOREGISTER,
    'threaded': settings.RPC_THREADED,
    'daemonize': settings.RPC_DAEMONIZE,
    'pidfile': settings.RPC_PIDFILE,
    'server_user': settings.RPC_SERVER_USER,
    'server_group': settings.RPC_SERVER_GROUP,
}


class Command(BaseCommand):
    help = "RPyC Server for OpenProximity."

    def handle(self, *args, **options):
        from django.conf import settings
        from django.utils import translation
        # Activate the current language, because it won't get activated later.
        try:
            translation.activate(settings.LANGUAGE_CODE)
        except AttributeError:
            pass
        runserver(args)

    def usage(self, subcommand):
        return self.help

def change_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    if not os.geteuid() == 0:
        # Do not try to change the gid/uid if not root.
        return
    (uid, gid) = get_uid_gid(uid, gid)
    os.setgid(gid)
    os.setuid(uid)

def get_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    import pwd, grp
    uid, default_grp = pwd.getpwnam(uid)[2:4]
    if gid is None:
        gid = default_grp
    else:
        try:
            gid = grp.getgrnam(gid)[2]
        except KeyError:
            gid = default_grp
    return (uid, gid)

def start_server(options):
    """
    Start RPyC server
    """

    if options['daemonize'] and options['server_user'] and options['server_group']:
        #ensure the that the daemon runs as specified user
        change_uid_gid(options['server_user'], options['server_group'])

    if options['threaded']:
	serv = ThreadedServer(server.OpenProximityService, options['host'],
	    port = options['port'], auto_register = options['autoregister'])
    else:
	print "Forking server is not a tested server!"
	serv = ForkingServer(server.OpenProximityService, options['host'],
	    port = options['port'], auto_register = options['autoregister'])

    try:
        serv.start()
    except KeyboardInterrupt:
        serv.stop()


def runserver(argset=[], **kwargs):
    # Get the options
    options = SERVER_OPTIONS.copy()
    options.update(kwargs)

    if options['daemonize']:
        if not options['pidfile']:
            options['pidfile'] = '/var/run/rpcserver_%s.pid' % options['port']

        from django.utils.daemonize import become_daemon
        become_daemon()

        fp = open(options['pidfile'], 'w')
        fp.write("%d\n" % os.getpid())
        fp.close()

    # Start the rpc server
    print 'starting server with options %s' % options
    start_server(options)

if __name__ == '__main__':
    runserver(sys.argv[1:])
