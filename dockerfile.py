#!/usr/bin/env pythen

"""Dockerfile related functions
"""

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

import re

# Parses the dockerfile (passed in as a string)
# and info to extract, and returns a list with the information in a more canonical form, still ordered.
def parse_dockerfile(contents):
	ret = []
	for l in contents.split('\n'):
		m = re.match("^[\s]*([A-Z]+)[\s]*(.*)$",l)
		if m:
			ret.append([m.group(1),m.group(2)])
			# Retained below for ref
			#if docker_command == "FROM":
			#	# In build.cnf, add the allowed_images.
			#	return [docker_command_args]

			#elif docker_command == "RUN":
			#	# Only handle simple commands for now and ignore the fact that Dockerfiles run 
			#	# with /bin/sh -c rather than bash.
			#	ret.append(docker_command_args)
			#elif docker_command == "ADD":
			#	# Send file - is this potentially got from the web? Is that the difference between this and COPY?
			#	ret.append(docker_command_args)
			#elif docker_command == "COPY":
			#	# Send file
			#	ret.append(docker_command_args)

			#elif docker_command == "CMD":
			#	# Only handle simple commands for now (ie not execs) and ignore the fact that Dockerfiles
			#	# Put in the run.sh
			#	return [docker_command_args]
			#elif docker_command == "EXPOSE":
			#	# Put in the run.sh
			#	ret.append(docker_command_args)
			#elif docker_command == "ENV":
			#	# Put in the run.sh
			#	ret.append(docker_command_args)
			#elif docker_command == "VOLUME":
			#	# Put in the run.sh
			#elif docker_command == "ENTRYPOINT":
			#	# Ignore - effectively the same as CMD for us.

			#elif docker_command == "USER":
			#	# Put in the start script
			#elif docker_command == "WORKDIR":
			#	# Put in the start script

			#elif docker_command == "ONBUILD":
			#	# Maps to finalize :)

			#elif docker_command == "MAINTAINER":
			#	# ?
			#	return [docker_command_args]
		else:
			print "Ignored line: " + line
	return ret

parse_dockerfile("""
a
A a
    B b
    c
""")


