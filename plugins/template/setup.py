from setuptools import setup
from plugin import __version__

setup(name="PluginName",
    version=__version__,
    packages=['plugin',],
    summary="Template Plugin",
    description="""A template plugin to create plugins from""",
    url="http://code.google.com/p/proximitymarketing/", 
)
