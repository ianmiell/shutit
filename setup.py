# To use a consistent encoding
from __future__ import print_function
from codecs import open
# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
	name='shutit',
	version='1.0.108',
	description='A programmable automation tool designed for complex builds',
	long_description='A programmable shell-based (pexpect) automation tool designed for complex builds. See: http://ianmiell.github.io/shutit',
	url='http://ianmiell.github.io/shutit/',
	author='Ian Miell',
	author_email='ian.miell@gmail.com',
	license='MIT',
	keywords='Docker pexpect expect automation build',
	packages=['shutit'],
	install_requires=['pexpect>=4.0','jinja2>=0.1','texttable>=0.1','six>=1.10','future>=0.15'],
	extras_require={
		'dev': [],
		'test': [],
	},
	package_data={},
	data_files=[],
	entry_points={
		'console_scripts': [
			'shutit=shutit.shutit:main',
		],
	},
)
