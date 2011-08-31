#!/usr/bin/env python

from django_cpserver.management.commands.runcpserver import CPSERVER_OPTIONS
from django.conf import settings

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

from django_cpserver.management.commands.runcpserver import Command
