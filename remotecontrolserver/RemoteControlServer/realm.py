# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.cred import portal
from zope.interface import implements
from user import ForwardUser

class ForwardRealm:
    """
        real that allows forward users, nothing fancy
    """
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        return interfaces[0], ForwardUser(avatarId), lambda: None
