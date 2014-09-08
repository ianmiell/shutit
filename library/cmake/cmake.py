"""ShutIt module. See http://shutit.tk

Based on: https://github.com/maidsafe/MaidSafe/wiki/Build-Instructions-for-Linux#all-other-prerequisites
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

class cmake(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        if shutit.cfg['container']['install_type'] == 'apt' and shutit.cfg['container']['distro'] == 'ubuntu':
            if shutit.cfg['container']['distro_version'] >= "14.04":
                shutit.install('cmake')
            else:
                shutit.install('gcc')
                shutit.install('g++')
                shutit.install('python-software-properties')
                shutit.install('git')
                shutit.install('make')
                shutit.send('pushd /opt')
                shutit.send('git clone git://cmake.org/cmake.git')
                shutit.send('pushd cmake')
                shutit.send('git checkout v2.8.12.2')
                shutit.send('./bootstrap')
                shutit.send('make')
                shutit.send('make install')
                shutit.send('popd')
                shutit.send('popd')
                shutit.add_to_bashrc("alias cmake='cmake -DCMAKE_C_COMPILER=gcc-4.8 -DCMAKE_CXX_COMPILER=g++-4.8'")
        return True

    def test(self, shutit):
        #shutit.send('cmake')
        return True


def module():
    return cmake(
        'shutit.tk.cmake.cmake', 782914092.09187246124,
        description='CMake',
        maintainer='ian.miell@gmail.com',
        depends=['shutit.tk.setup']
    )

