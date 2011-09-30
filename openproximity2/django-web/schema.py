# -*- coding: utf-8 -*-
import django, os, sys
from configglue.schema import ( Section, StringOption, IntOption, BoolOption,
                                DictOption, TupleOption, ListOption )
from django_configglue.schema import Django13Schema
from ConfigParser import MAX_INTERPOLATION_DEPTH

class _Context(object):
    def __init__(self, config, section):
        self.config = config
        self.section = section

    def __getitem__(self, key):
        if '.' in key:
            return self.config.get(*key.split('.'))
        else:
            return self.config.get(self.section, key)

def _interpolate(self, section, option, rawval, vars):
      # do the string interpolation
      value = rawval
      depth = MAX_INTERPOLATION_DEPTH
      while depth:                    # Loop through this until it's done
          depth -= 1
          if "%(" in value:
              value = self._KEYCRE.sub(self._interpolation_replace, value)
              try:
                  value = value % _Context(self, section)
              except KeyError, e:
                  raise InterpolationMissingOptionError(
                      option, section, rawval, e.args[0])
          else:
              break
      if "%(" in value:
          raise InterpolationDepthError(option, section, rawval)
      return value

class OpenProximitySchema(Django13Schema):
    ################################################
    # openproximity general settings
    ################################################
    openproximity = Section('openproximity')
    openproximity.aircable_path = StringOption( default='/tmp/aircable',
        help = 'Path were we store the database file (if using sqlite) and storing files for campaigns etc')
    openproximity.op2_debug = BoolOption(default=True,
        help = 'Disable if you want to hide the "Databrowse" tab')
    openproximity.op2_translate = BoolOption(default=True,
        help = 'Disable if you want to hide the "Translate" tab')
    openproximity.op2_twitter = BoolOption(default=True,
        help = 'Disable if you want to hide the Twitter news client')
    openproximity.op2_logo = StringOption(default='logo.gif',
        help = 'Logo to display instead of AIRcable logo')
    openproximity.op2_plugins = DictOption(item=BoolOption(),
        help="""A list of plugins name with they're enable/disable state overrides plugins defaults)""")
    openproximity.op2_scanners = ListOption( item=TupleOption(4),
        help="""A list of ([MAC filter], scanner priority) for dongle configuration on initial discovery""")
    openproximity.op2_uploaders = ListOption( item=TupleOption(4),
        help="""A list of ([MAC filter], max connections) for dongle configuration on initial discovery""")

    ################################################
    # cherrypy settings
    ################################################
    cherrypy = Section('cherrypy')
    cherrypy.cp_host = StringOption(default="localhost",
                                                  help='hostname to listen on')
    cherrypy.cp_port = IntOption(default=8088, help='port to listen on')
    cherrypy.cp_server_name = StringOption(default="localhost",
                                    help="CherryPy's SERVER_NAME environ entry")
    cherrypy.cp_daemonize = BoolOption(default = False,
                                        help='whether to detach from terminal')
    cherrypy.cp_pidfile = StringOption(default=None,
                              help="write the spawned process-id to this file")
    cherrypy.cp_workdir = StringOption(default=None,
                              help="change to this directory when daemonizing")
    cherrypy.cp_threads = IntOption(default=20,
                                    help='Number of threads for server to use')
    cherrypy.cp_ssl_certificate = StringOption(default=None,
                                                help="SSL certificate filename")
    cherrypy.cp_ssl_private_key = StringOption(default=None,
                                                help="SSL private key filename")
    cherrypy.cp_server_user = StringOption(default='www-data',
                                          help="user to run daemonized process")
    cherrypy.cp_server_group = StringOption(default='www-data',
                                            help="group to daemonized process")

    ################################################
    # rpyc settings
    ################################################
    rpyc = Section('rpyc')
    rpyc.rpc_host = StringOption(default="localhost",
                                                  help='hostname to listen on')
    rpyc.rpc_port = IntOption(default=8010, help='port to listen on')
    rpyc.rpc_daemonize = BoolOption(default = False,
                                        help='whether to detach from terminal')
    rpyc.rpc_threaded = BoolOption(default = True,
                                    help='run in threaded way instead of forked')
    rpyc.rpc_autoregister = BoolOption(default = False,
                                help='try registering the server in name servers')
    rpyc.rpc_pidfile = StringOption(default = None,
                              help="write the spawned process-id to this file")
    rpyc.rpc_server_user = StringOption(default='www-data',
                                          help="user to run daemonized process")
    rpyc.rpc_server_group = StringOption(default='www-data',
                                            help="group to daemonized process")

    ################################################
    # debugging settings
    ################################################
    debug = Section('debug')
    debug.debug_console = StringOption(default = 'INFO',
        help='console debug level, default INFO')
    debug.debug_level = StringOption(default = 'DEBUG',
        help='in file debug level, default DEBUG')
    debug.debug_path = StringOption(default='/var/log/openproximity',
        help='default path used for storing log files')
    debug.debug_maxsize = IntOption(default=10, 
        help='max log file in MB, defaults to 10')
    debug.debug_count = IntOption(default=5,
        help='amount of log files to store when rotating, defaults to 2')
    debug.debug_filename=StringOption(default=None,
        help='file name used for this debug session, defaults to sys.argv[1]')
    debug.debug_console_format = StringOption(
        default='%(name)s %(module)s:%(funcName)s: %(message)s',
        help='console log formatting')
    debug.debug_format = StringOption(
        default='%(asctime)-12s - %(levelname)5s - %(name)10s - %(funcName)-12s: %(message)s',
        help='file log formatting')
    debug.debug_disables = StringOption( default='', 
        help='comma separated list of disable log modules')

if os.path.isfile('/etc/timezone'):
    OpenProximitySchema.django.time_zone.default = file('/etc/timezone').readline().strip()

OpenProximitySchema.django.auth_profile_module = StringOption(default=None,
                              help="Module to use for authoring")
OpenProximitySchema.django.serialization_modules = DictOption(
                              help="Default empty dict")
