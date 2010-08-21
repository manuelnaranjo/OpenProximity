# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.conch import avatar
from twisted.conch.ssh import session, forwarding
from twisted.conch.ssh.forwarding import openConnectForwardingClient
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.conch.ssh.transport import DISCONNECT_RESERVED
from time import time
import struct

from checker import PublicKeyCredentialsChecker
from conf import config
import database

import os

MINUTES=60
if os.environ.has_key("DEBUG"):
    MINUTES=1
# how many seconds make up a minute, defined as variable for debugging purposes

def LoggedMonitor():
    print "Logged User Monitor: %s users" % len(ForwardUser.loggedin)

def AnnonTimeout(user=None, loop=None):
    loop.stop()
    print "AnnonTimeout for %s" % user
    user.conn.transport.sendDisconnect(DISCONNECT_RESERVED, 
                                       "Annonymous login expired")
    del ForwardUser.loggedin[user]    

class ForwardUser(avatar.ConchUser):
    """
        User that's has the needed methods to allow tcp forwarding
    """
    
    loggedin = dict()
    
    def __init__(self, username):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.listeners={}
        self.pubkey = PublicKeyCredentialsChecker.instance.getKey(username)
        self.isannon =  PublicKeyCredentialsChecker.instance.isAnnon(username) 

        self.channelLookup.update({
                'session':session.SSHSession,
                'direct-tpcip': openConnectForwardingClient
        })
        
        if self.isannon:
            if config["ANNONYMOUS_TIMEOUT"] > 0:
                repeater=LoopingCall(AnnonTimeout, user=self)
                repeater.kw['loop']=repeater
                repeater.start(config["ANNONYMOUS_TIMEOUT"]*MINUTES, now=False)
        
        if not database.getUser(key=self.pubkey):
            database.createUser(key=self.pubkey, 
                                username=self.username, 
                                enabled=not self.isannon)
        # log user logged in
        database.updateUserLastLogin(key=self.pubkey)
        ForwardUser.loggedin[self]=time()

    def global_tcpip_forward(self, data):
        hostToBind, portToBind = forwarding.unpackGlobal_tcpip_forward(data)
        print "forward requested", hostToBind, portToBind
        try: 
            listener = reactor.listenTCP( 
                    portToBind, 
                    forwarding.SSHListenForwardingFactory(
                                self.conn,
                                (hostToBind, portToBind),
                                forwarding.SSHListenServerForwardingChannel), 
                    interface = hostToBind)
        except:
            return 0
        else:
            generated=False
            if portToBind == 0:
                portToBind = listener.getHost()[2] # the port
                print "generating port number", portToBind
                generated=True
            
            self.listeners[(hostToBind, portToBind)] = listener
            if generated:
                return 1, struct.pack('>L', portToBind)
            else:
                return 1

    def global_cancel_tcpip_forward(self, data):
        hostToBind, portToBind = forwarding.unpackGlobal_tcpip_forward(data)
        print "forward cancel requested", portToBind
        
        listener = self.listeners.get((hostToBind, portToBind), None)
        if not listener:
            return 0
        
        del self.listeners[(hostToBind, portToBind)]
        listener.stopListening()
        return 1
    
    def annon_disconnect(self):
        del ForwardUser.loggedin[self]
        self.conn.transport.sendDisconnect(DISCONNECT_RESERVED, 
                                           "Annonymous login expired")
        self.logOut()
    
    def logOut(self):
        self.updateAccumulatedTime()
        
    def updateAccumulatedTime(self):
        database.updateUserAccumulatedTime(self.pubkey)
        
    def __str__(self):
        return "%s, %s" % ( self.username, self.isannon)

repeater=LoopingCall(LoggedMonitor)
repeater.start(10, now=False)
