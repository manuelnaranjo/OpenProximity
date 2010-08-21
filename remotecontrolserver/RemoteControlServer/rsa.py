# -*- coding: utf-8 -*-

# Copyright (c) 2010 Naranjo Manuel Francisco manuel@aircable.net
# Copyright (c) 2009 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.python.randbytes import secureRandom
from twisted.conch.ssh import keys
import os
from conf import config

def getRSAKeys():
    """
        will return a pair of publicKeyString, privateKeyString for the running
        server, will generate the pair if this aren't available
    """
    pub = os.path.join(config["RSA_STORAGE"], 'public.key')
    priv = os.path.join(config["RSA_STORAGE"], 'private.key')
    if not (os.path.exists(pub) and os.path.exists(priv)):
        print "Generating RSA keypair..."
        
        from Crypto.PublicKey import RSA
        KEY_LENGTH = 1024
        rsaKey = RSA.generate(KEY_LENGTH, secureRandom)
        
        publicKeyString = keys.Key(rsaKey).public().toString('openssh', '')
        privateKeyString = keys.Key(rsaKey).toString('openssh', '')
        
        print "Saving RSA keypair..."
        file(pub, 'w+b').write(publicKeyString)
        file(priv, 'w+b').write(privateKeyString)
        print "done."
    else:
        print "RSA keypair found"
        publicKeyString = file(pub).read()
        privateKeyString = file(priv).read()
    return publicKeyString, privateKeyString
