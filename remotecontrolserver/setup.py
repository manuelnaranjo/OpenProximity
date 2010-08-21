'''
Created on 01/03/2010

@author: manuel
'''

from setuptools import setup                                                        
from RemoteControlServer import __version__                                                   

setup(name="RemoteControlServer",
    version=__version__,
    packages=[
        'RemoteControlServer'
    ],
    description="""Remote Control System - Server""",
    long_description="""ssh based application created to allow remote control of
customer computers""",
    author="Naranjo Manuel Francisco",
    author_email= "manuel@aircable.net",
    license="LGPL",
    scripts=['remotecontrolserver',],
    url="http://code.google.com/p/aircable/",
    platform="linux",
)
