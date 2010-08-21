#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.



"""
Forward only server

This server only allows to do tcp port forwarding over
a secure channel
"""
def start():
    from checker import PublicKeyCredentialsChecker
    from factory import ForwardFactory
    from realm import ForwardRealm
    from session import ForwardSession
    from twisted.conch.ssh import session
    from twisted.cred import portal
    from twisted.internet import reactor
    from twisted.python import components, log
    from user import ForwardUser
    from conf import config
    import sys
    
    log.startLogging(sys.stderr)
    
    components.registerAdapter(ForwardSession, ForwardUser, session.ISession)

    portal = portal.Portal(ForwardRealm())
    portal.registerChecker(PublicKeyCredentialsChecker())
    ForwardFactory.portal = portal
    print "running server on %s:%s" % (config['SSH_INTERFACE'],config['SSH_PORT'])
    reactor.listenTCP(
                  port=config['SSH_PORT'], 
                  interface=config['SSH_INTERFACE'], 
                  factory=ForwardFactory()
        )
    reactor.run()

if __name__=='__main__':
    start()
