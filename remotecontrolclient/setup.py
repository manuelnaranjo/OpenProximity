'''
Created on 01/03/2010

@author: manuel
'''

from setuptools import setup                                                        
from RemoteControlClient import __version__                                                   

setup(name="RemoteControlClient",
    version=__version__,
    packages=[
        'RemoteControlClient'
    ],
    description="""Remote Control System - Client""",
    long_description="""ssh based application created to allow remote control of
customer computers""",
    author="Naranjo Manuel Francisco",
    author_email= "manuel@aircable.net",
    license="LGPL",
    scripts=['remotecontrolclient',],
    url="http://code.google.com/p/aircable/",
    platform="linux",
)
