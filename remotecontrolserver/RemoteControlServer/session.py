# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from user import ForwardUser

class ForwardSession:
    """
      A session that will only allow port forwarding by just not providing 
      pty, execCommand or shell
    """
    
    def __init__(self, avatar):
        self.user = avatar

    def getPty(self, term, windowSize, attrs):
        raise Exception("no pty")
    
    def execCommand(self, proto, cmd):
        raise Exception("no executing commands")

    def openShell(self, trans):
        raise Exception("no shell")

    def __delUser(self):
        pass

    def eofReceived(self):
        print "eof received"

    def closed(self):
        print "connection closed"
        self.user.logOut()
