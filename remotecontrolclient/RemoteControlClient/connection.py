# Copyright (c) 2010 Naranjo Manuel Francisco <manuel@aircable.net>
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.conch.error import ConchError
from twisted.conch.ssh import connection, forwarding
from twisted.python import log

__all__=['ForwardOnlySSHConnection', 'SSHListenClientForwardingChannel']

class ForwardOnlySSHConnection(connection.SSHConnection):
    '''
    an ssh connection that's capable of remote port forwarding
    '''
    onConnect=lambda x: None
    stopConnection=lambda x: None
    
    def register_onConnect(self, func):
        self.onConnect=func
    
    def register_stopConnection(self, func):
        self.stopConnection = func
    
    def serviceStarted(self):
        global conn
        conn = self
        self.remoteForwards = {}
        if not isinstance(self, connection.SSHConnection):
            # make these fall through
            del self.__class__.requestRemoteForwarding
            del self.__class__.cancelRemoteForwarding
        self.onConnect()

    def serviceStopped(self):
        self.stopConnection()

    def requestRemoteForwarding(self, remotePort, hostport):
        '''
        will get called when the remote forwarding request gets started
        '''
        data = forwarding.packOpen_direct_tcpip(('0.0.0.0',remotePort),hostport)
        d = self.sendGlobalRequest('tcpip-forward', data, wantReply=1)
        log.msg('requesting remote forwarding %s:%s' %(remotePort, hostport))
        d.addCallback(self._cbRemoteForwarding, remotePort, hostport)
        d.addErrback(self._ebRemoteForwarding, remotePort, hostport)

    def _cbRemoteForwarding(self, result, remotePort, hostport):
        '''
        remote port forwarding accepted
        '''

        log.msg('accepted remote forwarding %s:%s' % (remotePort, hostport))
        self.remoteForwards[remotePort] = hostport
        log.msg(repr(self.remoteForwards))
    
    def _ebRemoteForwarding(self, f, remotePort, hostport):
        '''
        remote port forwarding failed
        '''
        log.msg('remote forwarding %s:%s failed' % (remotePort, hostport))
        log.msg(f)

    def cancelRemoteForwarding(self, remotePort):
        '''
        call this method to cancel a remote port forwarding
        '''
        data = forwarding.packGlobal_tcpip_forward(('0.0.0.0', remotePort))
        self.sendGlobalRequest('cancel-tcpip-forward', data)
        log.msg('cancelling remote forwarding %s' % remotePort)
        try:
            del self.remoteForwards[remotePort]
        except:
            pass
        log.msg(repr(self.remoteForwards))

    def channel_forwarded_tcpip(self, windowSize, maxPacket, data):
        '''
        This gets called when the remote forwared port gets a connection request
        '''
        log.msg('%s %s' % ('FTCP', repr(data)))
        remoteHP, origHP = forwarding.unpackOpen_forwarded_tcpip(data)
        log.msg(self.remoteForwards)
        log.msg(remoteHP)
        if self.remoteForwards.has_key(remoteHP[1]):
            connectHP = self.remoteForwards[remoteHP[1]]
            log.msg('connect forwarding %s' % (connectHP,))
            return SSHConnectForwardingChannel(connectHP,
                                            remoteWindow = windowSize,
                                            remoteMaxPacket = maxPacket,
                                            conn = self)
        else:
            raise ConchError(connection.OPEN_CONNECT_FAILED, "don't know about that port")

    def channelClosed(self, channel):
        '''
        will get called when ssh channel is closed
        '''
        log.msg('connection closing %s' % channel)
        log.msg(self.channels)
        if len(self.channels) == 1:
            log.msg('stopping connection')
            self.stopConnection()
        else:
            # because of the unix thing
            self.__class__.__bases__[0].channelClosed(self, channel)

class SSHListenClientForwardingChannel(forwarding.SSHListenClientForwardingChannel): pass
class SSHConnectForwardingChannel(forwarding.SSHConnectForwardingChannel): pass
