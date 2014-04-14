#!/bin/bash
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
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
set -e
python ../../shutit_main.py
# Display config
#python /space/git/shutit/bin/../shutit_main.py --sc
# Debug
#python /space/git/shutit/bin/../shutit_main.py --debug
# Tutorial
#python /space/git/shutit/bin/../shutit_main.py --tutorial
# Push command line example
#python ../../shutit_main.py -s repository do_repository_work yes -s repository push yes -s repository server "" -s repository name get_iplayer -s repository user imiell -s repository suffix_date yes -s repository password XXX -s repository email ian.miell@gmail.com -s repository suffix_format '%Y%m%d'

