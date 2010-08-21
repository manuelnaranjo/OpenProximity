'''

Forward only ssh client, targeted for remote control systems, mainly targeting
remote support applications



Copyright (c) 2010 Naranjo Manuel Francisco <manuel@aircable.net>

Copyright (c) 2009 Twisted Matrix Laboratories.
'''

from twisted.conch.client import options
from twisted.internet import reactor
from twisted.python import log, usage
from getpass import getuser
import sys

from transport import connect

class ClientOptions(usage.Options):
    synopsis = """Usage:   %s [options] host [command]
""" % sys.argv[0]
    
    optParameters = [
                ['user', 'l', None, 'Log in using this user name.'],
                ['port', 'p', None, 'Connect to this port.  Server must be on the same port.'],
                ['remoteforward', 'R', None, 'listen-port:host:port   Forward remote port to local address'],
                ['logfile', 'L', None, 'Store log to this file'],
            ]

    zsh_actionDescr = {"remoteforward":"listen-port:host:port"}
    zsh_extras = ["*:command: "]

    remoteForwards = []

    def opt_escape(self, esc):
        "Set escape character; ``none'' = disable"
        if esc == 'none':
            self['escape'] = None
        elif esc[0] == '^' and len(esc) == 2:
            self['escape'] = chr(ord(esc[1])-64)
        elif len(esc) == 1:
            self['escape'] = esc
        else:
            sys.exit("Bad escape character '%s'." % esc)

    def opt_remoteforward(self, f):
        """Forward remote port to local address (rport:host:port)"""
        remotePort, connHost, connPort = f.split(':') # doesn't do v6 yet
        remotePort = int(remotePort)
        connPort = int(connPort)
        self.remoteForwards.append((remotePort, (connHost, connPort)))

    def parseArgs(self, host, *command):
        self['host'] = host
        self['command'] = ' '.join(command)

def start():
    global options, old
    args = sys.argv[1:]

    options = ClientOptions()
    try:
        options.parseOptions(args)
    except usage.UsageError, u:
        print 'ERROR: %s' % u
        options.opt_help()
        sys.exit(1)
    
    log.startLogging(sys.stderr)
    if options['logfile']:
	from twisted.python.log import FileLogObserver, addObserver
	addObserver(FileLogObserver(open(options['logfile'], 'w')).emit)

    if options['host'].find('@') >-1:
        options['user'],options['host']=options['host'].split('@',1)
    
    if not options['user']:
        options['user']=getuser()
    
    if not options['port']:
        options['port']='22' 
    
    connect(options['host'], options['port'], options)
    
    reactor.run()
    print 'Connection to %s closed.' % options['host']
    sys.exit()

if __name__=="__main__":
    start()
