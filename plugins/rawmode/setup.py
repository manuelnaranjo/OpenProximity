from setuptools import setup
from rawmode import __version__

setup(name="Raw Mode",
    version=__version__,
    packages=[
	'rawmode',
    ],
    summary="Raw mode",
    description="""Raw mode plugin""",
    long_description="""A small plugins that allows users to manually send a 
file to a certain target, it works with non AIRcable dongles""",
    author="Naranjo Manuel Francisco",
    author_email= "manuel@aircable.net",
    package_dir={'rawmode': 'rawmode',},
    package_data={
	'rawmode': [
	    'templates/rawmode/*', 
	]},
    license="GPL2",
    url="http://code.google.com/p/proximitymarketing/", 
)
