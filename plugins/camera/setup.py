from setuptools import setup
from camera import __version__

setup(name="Camera",
    version=__version__,
    packages=[
	'camera',
	'camera.templatetags',
    ],
    summary="Camera Manager",
    description="""Camera plugin""",
    long_description="""Simple plugin that will connect to the available 
bluetooth Cameras(OptiEyes so far) one at the time take pictures for 1 
minute and then go to the next one.
""",
    author="Naranjo Manuel Francisco",
    author_email= "manuel@aircable.net",
    package_dir={'camera': 'camera',},
    package_data={
	'camera': [
	    'templates/camera/*', 
	    'templates/admin/camera/*',
	    'media/*', 
	]},
    license="GPL2",
    url="http://code.google.com/p/aircable/", 
)
