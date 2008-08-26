#!/usr/bin/env python

from distutils.core import setup

setup(name='OpenProximity',
	version='0.2',
	description='OpenProximity by AIRcable',
	author='Naranjo Manuel Francisco',
	author_email='manuel@aircable.net',
	package_dir= {'' : 'src' } ,
	url='www.aircable.net',
	packages=['net.aircable'],
	scripts=['src/openproximity.py'],
	license="Apache version 2",
    )
    
