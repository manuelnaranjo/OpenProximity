# Copyright (c) 2010 Naranjo Manuel Francisco <manuel@aircable.net>
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.conch.ssh import transport
from twisted.internet import defer, protocol, reactor

from auth import ForwardOnlyUserAuth
from connection import ForwardOnlySSHConnection

class ForwardOnlyTransport(transport.SSHClientTransport):
    '''
    transport used to stablish the connection over ssh, it will allow only
    remote port forwarding, no hostkey verification is done.
    '''
    def __init__(self, options, *args, **kwargs):
        self.options = options
        self.conn = None
        self.user= options['user']
        
    def verifyHostKey(self, hostKey, fingerprint):
        """just say it's fine to use this key"""
        print 'host key fingerprint: %s' % fingerprint
        return defer.succeed(True) 

    def connectionSecure(self):
        '''
        called when the ssh link is created, login now, then handle control
        to ForwardOnlySSHConnection
        '''
        self.conn=ForwardOnlySSHConnection()
        self.conn.register_onConnect(self.OnConnect)
        self.requestService(
            ForwardOnlyUserAuth(self.user,self.conn)
            )

    def OnConnect(self):
        """
        connected and logged in, it's time to forward the ports
        """
        if self.options.remoteForwards:
            for remotePort, hostport in self.options.remoteForwards:
                print 'asking for remote forwarding for %s:%s' % (remotePort, 
                                                                  hostport)
                self.conn.requestRemoteForwarding(remotePort, hostport)
            #reactor.addSystemEventTrigger('before', 'shutdown', beforeShutdown)


class ForwardOnlyFactory(protocol.ClientFactory):
    """
    Transport factory
    """
    
    def __init__(self, username, *args, **kwargs):
        self.username = username
    
    def buildProtocol(self, addr):
        protocol = ForwardOnlyTransport(self.username)
        return protocol
    
    def clientConnectionFailed(self, connector, reason):
        """
        inform user connection failed then stop reactor
        """ 
        print "connection failed", reason
        try: reactor.stop()
        except: pass
    
    def clientConnectionLost(self, connector, reason):
        """
        inform user we lost connection then stop reactor
        """ 
        print "connection failed", reason
        try: reactor.stop()
        except: pass
        
def connect(host='127.0.0.1', port='5022', options={}):
    """
    use this method to create a new connection
    """
    factory=ForwardOnlyFactory(options)
    reactor.connectTCP(host, int(port), factory)
