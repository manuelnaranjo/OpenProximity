# -*- coding: utf-8 -*-
import django, os
from configglue.pyschema import ( ConfigSection, StringConfigOption,
        IntConfigOption, BoolConfigOption, DictConfigOption, LinesConfigOption,
        TupleConfigOption )
from django_configglue.schema import Django112Schema
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

class OpenProximitySchema(Django112Schema):
    ################################################
    # openproximity general settings
    ################################################
    openproximity = ConfigSection('openproximity')
    openproximity.aircable_path = StringConfigOption( default='/tmp/aircable',
        help = 'Path were we store the database file (if using sqlite) and storing files for campaigns etc')
    openproximity.op2_debug = BoolConfigOption(default=True,
        help = 'Disable if you want to hide the "Databrowse" tab')
    openproximity.op2_translate = BoolConfigOption(default=True,
        help = 'Disable if you want to hide the "Translate" tab')
    openproximity.op2_twitter = BoolConfigOption(default=True,
        help = 'Disable if you want to hide the Twitter news client')
    openproximity.op2_logo = StringConfigOption(default='logo.gif',
        help = 'Logo to display instead of AIRcable logo')
    openproximity.op2_plugins = DictConfigOption(item=BoolConfigOption(),
        help="""A list of plugins name with they're enable/disable state overrides plugins defaults)""")
    openproximity.op2_scanners = LinesConfigOption( item=TupleConfigOption(4),
        help="""A list of ([MAC filter], scanner priority) for dongle configuration on initial discovery""")
    openproximity.op2_uploaders = LinesConfigOption( item=TupleConfigOption(4),
        help="""A list of ([MAC filter], max connections) for dongle configuration on initial discovery""")

    ################################################
    # cherrypy settings
    ################################################
    cherrypy = ConfigSection('cherrypy')
    cherrypy.cp_host = StringConfigOption(default="localhost",
                                                  help='hostname to listen on')
    cherrypy.cp_port = IntConfigOption(default=8088, help='port to listen on')
    cherrypy.cp_server_name = StringConfigOption(default="localhost",
                                    help="CherryPy's SERVER_NAME environ entry")
    cherrypy.cp_daemonize = BoolConfigOption(default = False,
                                        help='whether to detach from terminal')
    cherrypy.cp_pidfile = StringConfigOption(default=None,
                              help="write the spawned process-id to this file")
    cherrypy.cp_workdir = StringConfigOption(default=None,
                              help="change to this directory when daemonizing")
    cherrypy.cp_threads = IntConfigOption(default=20,
                                    help='Number of threads for server to use')
    cherrypy.cp_ssl_certificate = StringConfigOption(default=None,
                                                help="SSL certificate filename")
    cherrypy.cp_ssl_private_key = StringConfigOption(default=None,
                                                help="SSL private key filename")
    cherrypy.cp_server_user = StringConfigOption(default='www-data',
                                          help="user to run daemonized process")
    cherrypy.cp_server_group = StringConfigOption(default='www-data',
                                            help="group to daemonized process")

    ################################################
    # rpyc settings
    ################################################
    rpyc = ConfigSection('rpyc')
    rpyc.rpc_host = StringConfigOption(default="localhost",
                                                  help='hostname to listen on')
    rpyc.rpc_port = IntConfigOption(default=8010, help='port to listen on')
    rpyc.rpc_daemonize = BoolConfigOption(default = False,
                                        help='whether to detach from terminal')
    rpyc.rpc_threaded = BoolConfigOption(default = True,
                                    help='run in threaded way instead of forked')
    rpyc.rpc_autoregister = BoolConfigOption(default = False,
                                help='try registering the server in name servers')
    rpyc.rpc_pidfile = StringConfigOption(default=None,
                              help="write the spawned process-id to this file")
    rpyc.rpc_server_user = StringConfigOption(default='www-data',
                                          help="user to run daemonized process")
    rpyc.rpc_server_group = StringConfigOption(default='www-data',
                                            help="group to daemonized process")


if os.path.isfile('/etc/timezone'):
    OpenProximitySchema.django.time_zone.default = file('/etc/timezone').readline().strip()

OpenProximitySchema.django.auth_profile_module = StringConfigOption(default=None,
                              help="Module to use for authoring")
OpenProximitySchema.django.serialization_modules = DictConfigOption(help="Default empty dict")
