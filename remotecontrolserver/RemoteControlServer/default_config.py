ALLOW_ANNONYMOUS = (True, bool)
ANNONYMOUS_TIMEOUT = (30, int)   
# in minutes
    
SSH_PORT = (5555, int)
SSH_INTERFACE= ("", lambda x: x)
# all interfaces

WEB_PORT = (8000, int)
WEB_INTERFACE = ("", lambda x: x)          
# all interfaces

RSA_STORAGE=("/tmp/", lambda x: x)
