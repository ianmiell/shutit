#Copyright (C) 2014 OpenBet Limited
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

class get_iplayer(ShutItModule):

    def build(self, shutit):
        if shutit.cfg['container']['install_type'] == 'yum':
            shutit.install('wget')
            shutit.send('wget http://linuxcentre.net/get_iplayer/packages/get_iplayer-current.noarch.rpm')
            shutit.send('yum --nogpgcheck localinstall get_iplayer-current.noarch.rpm')
        else:
            shutit.install('git')
            shutit.install('liblwp-online-perl')
            shutit.install('rtmpdump')
            shutit.install('ffmpeg')
            shutit.install('mplayer')
            shutit.install('atomicparsley')
            shutit.install('id3v2')
            shutit.install('libmp3-info-perl')
            shutit.install('libmp3-tag-perl')
            shutit.install('libnet-smtp-ssl-perl')
            shutit.install('libnet-smtp-tls-butmaintained-perl')
            shutit.install('libxml-simple-perl')
            shutit.send('pushd /')
            shutit.send('git clone git://git.infradead.org/get_iplayer.git')
            shutit.send('cd get_iplayer')
            shutit.send('chmod 755 get_iplayer')
            shutit.send('./get_iplayer')
            shutit.send('popd')
        return True

    def is_installed(self, shutit):
        return shutit.file_exists('/get_iplayer/get_iplayer')

def module():
    return get_iplayer(
        'shutit.tk.get_iplayer.get_iplayer', 0.324,
        description='iPlayer downloader. See ' +
            'http://www.infradead.org/get_iplayer/html/get_iplayer.html',
        depends=['shutit.tk.setup']
    )

