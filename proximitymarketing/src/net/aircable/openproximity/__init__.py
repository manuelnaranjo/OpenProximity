import os
from string import lower

obex_ftp = False;

if 'USE_OBEXFTP' in os.environ.keys():
    obex_ftp = lower(os.environ['USE_OBEXFTP']) == 'yes'
