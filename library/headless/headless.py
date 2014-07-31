"""ShutIt module. See http://shutit.tk
"""
#Copyright (C) 2014 OpenBet Limited
#
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is furnished
#to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule

class headless(ShutItModule):

    def is_installed(self,shutit):
        return False

    def build(self,shutit):
        shutit.install('xvfb')
        shutit.install('rubygems')
        shutit.send('gem install headless')
        return True

def module():
    return headless(
        'shutit.tk.headless.headless', 0.1231251,
        description='https://github.com/mparaz/headless',
        depends=['shutit.tk.setup']
    )

