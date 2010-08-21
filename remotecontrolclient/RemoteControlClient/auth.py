# Copyright (c) 2010 Naranjo Manuel Francisco <manuel@aircable.net>
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.conch.ssh import userauth, keys
from twisted.internet import defer
import os

def getRSAKeys():
    """
        will return a pair of publicKeyString, privateKeyString for the running
        server, will generate the pair if this aren't available
    """
    from twisted.python.randbytes import secureRandom
    from Crypto.PublicKey import RSA
    KEY_LENGTH = 1024
    rsaKey = RSA.generate(KEY_LENGTH, secureRandom)
    
    publicKeyString = keys.Key(rsaKey).public().toString("openssh", '')
    privateKeyString = keys.Key(rsaKey).public().toString("openssh", '')
    
    return publicKeyString, privateKeyString


class ForwardOnlyUserAuth(userauth.SSHUserAuthClient):
    '''
    an rsa key only auth client, if no keys are available they are generated
    '''
    def __init__(self, user=None, instance=None, id_file=None):
        userauth.SSHUserAuthClient.__init__(self, user, instance)
        self.id_file=id_file or os.path.expanduser('~/.ssh/id_rsa')
        
        if os.path.exists(self.id_file):
            print "Found keys for user %s" % user
            #key=file(self.id_file+'.pub', 'r').read()
            self.publicKey = file(self.id_file+'.pub', 'r').read()
            self.privateKey = file(self.id_file, 'r').read()
        else:
            print "Creating keys for user %s" % user
            self.publicKey, self.privateKey = getRSAKeys()

        self.publicKey = keys.Key.fromString(self.publicKey).blob()
        self.privateKey = keys.Key.fromString(self.privateKey).keyObject

    def getPublicKey(self): 
        if self.lastPublicKey:
            # the file doesn't exist, or we've tried a public key
            return
        return self.publicKey

    def getPrivateKey(self):
        return defer.succeed(keys.getPrivateKeyObject(self.id_file))

