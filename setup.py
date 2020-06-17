# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in frappe_renovation_docsync/__init__.py
from frappe_renovation_docsync import __version__ as version

setup(
	name='frappe_renovation_docsync',
	version=version,
	description='Extensions for Frappe Event Streams',
	author='Leam Technology Systems',
	author_email='info@leam.ae',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
