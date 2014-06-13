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

class squid_deb_proxy(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		# This sets up the avahi daemon such that the squid deb proxy can run.
		# TODO: separate into its own module.
		shutit.install('avahi-daemon')
		shutit.send_and_expect('mkdir -p /var/run/dbus/')
		# pw user add messagebus # was in original instruction, didn't work, apparently not needed
		shutit.send_and_expect('dbus-daemon --system')
		shutit.send_and_expect('/usr/sbin/avahi-daemon &')
		shutit.send_file('/root/start_avahi_daemon.sh', '''
			dbus-daemon --system
			/usr/sbin/avahi-daemon &
		''')
		shutit.send_file('/root/start_avahi_daemon.sh', '''
			# TODO stop these
			#dbus-daemon --system
			#/usr/sbin/avahi-daemon &
		''')
		# TODO: add to start/stop script
		# We seem to need to remove this so that our settings work. Since this is not a "real" machine, I think.
		shutit.install('netcat')
		shutit.install('net-tools')
		shutit.install('squid-deb-proxy-client')
		return True

	def start(self,shutit):
		shutit.send_and_expect('rm -f /usr/share/squid-deb-proxy-client/apt-avahi-discover')
		shutit.send_and_expect("""route -n | awk '/^0.0.0.0/ {print $2}' | tee /tmp/hostip""",check_exit=False)
		shutit.send_and_expect("""echo "HEAD /" | nc `cat /tmp/hostip` """ + shutit.cfg['shutit.tk.squid_deb_proxy.squid_deb_proxy']['host_proxy_port'] + """ | grep squid-deb-proxy && (echo "Acquire::http::Proxy \\"http://$(cat /tmp/hostip):""" + shutit.cfg['shutit.tk.squid_deb_proxy.squid_deb_proxy']['host_proxy_port'] + """\\";" > /etc/apt/apt.conf.d/30proxy) && (echo "Acquire::http::Proxy::ppa.launchpad.net DIRECT;" >> /etc/apt/apt.conf.d/30proxy) || echo 'No squid-deb-proxy detected on docker host'""",check_exit=True)
		shutit.send_and_expect('rm -f /tmp/hostip')
		shutit.send_and_expect('/root/start_mysql.sh',check_exit=False)
		return True

	def stop(self,shutit):
		shutit.send_and_expect('/root/stop_mysql.sh',check_exit=False)
		return True

	def get_config(self,shutit):
		shutit.get_config('shutit.tk.squid_deb_proxy.squid_deb_proxy','host_proxy_port','8000')
		return True

def module():
	return squid_deb_proxy(
		'shutit.tk.squid_deb_proxy.squid_deb_proxy', 0.01,
		depends=['shutit.tk.setup']
	)

