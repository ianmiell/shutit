#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

"""Stores known package maps for different distributions.
"""

# Structured by package, then another dict with install_type -> mapped package inside that.
# The keys are then the canonical package names.
# eg {'httpd',
package_map = {'apache2':{'apt':'apache2','yum':'httpd'}}

def map_package(package,install_type):
	# If package mapping exists, then return it, else return package.
	global package_map
	if package in package_map.keys():
		for d in package_map[package].keys():
			if d == install_type:
				return package_map[package][install_type]
	# Otherwise, simply return package
	return package

# Is this name mentioned anywhere? Then return it as a suggestion?
def find_package(sought_package):
	global package_map
	# First check top-level keys
	if sought_package in package_map.keys():
		return package_map[sought_package]
	for package in package_map.keys():
		for install_type in package_map[package].keys():
			print package_map[package][install_type]
			if sought_package == package_map[package][install_type]:
				return {package:package_map[package]}
	return None
