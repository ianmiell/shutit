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
import os

class apache_proxypass(ShutItModule):
	
	def build(self, shutit):
		# Based on: http://www.jamescoyle.net/how-to/116-simple-apache-reverse-proxy-example
		shutit.install('apache2')
		# Let's use a value as a separator unlikely to be in the config for the host (@) to avoid perl compilation errors due to a clash.
		shutit.send('perl -p -i -e "s@<VirtualHost .:80>.*@<VirtualHost *:80>\nProxyHTMLStripComments on\nProxyRequests off\nSetOutputFilter proxy-html\nProxyHTMLDoctype XHTML\n<Location />\nProxyPass ' + shutit.cfg[self.module_id]['proxypass_site'] + '\nProxyPassReverse ' + shutit.cfg[self.module_id]['proxypass_site'] + '\nOrder allow,deny\nAllow from all\n</Location>@" /etc/apache2/sites-enabled/000-default')
		shutit.install('libapache2-mod-proxy-html')
		shutit.install('wget')
		shutit.send('a2enmod proxy_http')
		shutit.send('a2enmod proxy_html')
		shutit.send('service apache2 restart')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'proxypass_site','http://shutit.tk')
		return True

	def start(self, shutit):
		# example of starting something
		shutit.send('apache2ctl start')
		return True

	def stop(self, shutit):
		shutit.send('apache2ctl stop')
		return True

def module():
	return apache_proxypass(
		'shutit.tk.apache_proxypass.apache_proxypass', 0.310,
		description='example apache proxy-pass configuration',
		depends=['shutit.tk.setup']
	)

