# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.conch import error
from twisted.conch.ssh import keys
from twisted.cred import credentials, checkers
from twisted.python import failure
from zope.interface import implements

from random import Random
import string

from conf import config
import database

class PublicKeyCredentialsChecker:
    """
    first it will check if the user is allowed to access, if it's not then
    we login as ANNON
    """
    
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.ISSHPrivateKey,)
    instance = None
    
    def isAnnon(self, username):
        return username in self.annons
    
    def getKey(self, username):
        if self.isAnnon(username):
            return self.annons[username]
        return database.getUser(username=username)[0]['key']
    
    def __init__(self, authorizedKeys=None):
        self.authorizedKeys = authorizedKeys or {}
        self.annons = {}
        PublicKeyCredentialsChecker.instance = self
        
    def requestAvatarId(self, credentials):
        print "requestAvatarId", credentials.username
        user = database.getUser(key=credentials.blob)
        if user:
            if not user['enabled']:
                return failure.Failure(
                               error.ConchError("User account not enabled"))
            
            if not credentials.signature:
                return failure.Failure(error.ValidPublicKey())
            
            pubKey = keys.Key.fromString(credentials.blob).keyObject
            if keys.verifySignature(pubKey, credentials.signature,
                                    credentials.sigData):
                print "login as %s" % credentials.username
                database.updateUserName(credentials.blob, credentials.username)
                return credentials.username
            else:
                return failure.Failure(
                    error.ConchError("Incorrect signature"))

        elif config['ALLOW_ANNONYMOUS']:
            print "login as ANONYMOUS"
            user = "".join(Random().sample(string.letters,30))
            self.annons[user] = credentials.blob
            return user
        
        return failure.Failure(error.ConchError("Not allowed"))
