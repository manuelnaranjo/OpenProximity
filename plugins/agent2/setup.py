from setuptools import setup
from agent2 import __version__

setup(name="openproximity-agent2",
    version=__version__,
    packages=['agent2',
            'agent2.management', 
	    'agent2.management.commands', ],
    package_dir={'agent2': 'agent2',},
    package_data={
	'agent2': [
            'templates/agent2/*', 
    ]},
    summary="OpenProximity Agent2",
    description="""A data collector that pushes records into a centralized server.""",
    author="Naranjo Manuel Francisco",
    author_email= "manuel@aircable.net",
    license="GPL2",
    url="http://code.google.com/p/proximitymarketing", 
)
