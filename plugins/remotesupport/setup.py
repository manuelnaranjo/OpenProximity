from setuptools import setup
from remotesupport import __version__

setup(name="RemoteControlPlugin",
    version=__version__,
    packages=['remotesupport',],
    summary="Remote Control Plugin",
    description="""A plugin that allows customers to get remote support""",
    author="Naranjo Manuel Francisco",
    author_email= "manuel@aircable.net",
    license="GPL2",
    url="http://code.google.com/p/proximitymarketing/", 
)
