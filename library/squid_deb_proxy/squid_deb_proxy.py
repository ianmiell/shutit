"""ShutIt module. See http://shutit.tk
"""
from shutit_module import ShutItModule
import os

class squid_deb_proxy(ShutItModule):

	def build(self, shutit):
		# This sets up the avahi daemon such that the squid deb proxy can run.
		# TODO: separate into its own module.
		shutit.install('avahi-daemon')
		shutit.send('mkdir -p /var/run/dbus/')
		# pw user add messagebus # was in original instruction, didn't work, apparently not needed
		shutit.send('dbus-daemon --system')
		shutit.send('/usr/sbin/avahi-daemon &')
		shutit.send_file('/root/start_avahi_daemon.sh', '''
			dbus-daemon --system
			/usr/sbin/avahi-daemon &
		''')
		shutit.send_file('/root/stop_avahi_daemon.sh', '''
			ps -ef | grep avahi-daemon | awk '{print $1}' | xargs --no-run-if-empty kill
		''')
		shutit.send('chmod +x /root/start_avahi_daemon.sh')
		shutit.install('netcat')
		shutit.install('net-tools')
		shutit.install('squid-deb-proxy-client')
		shutit.send('/root/start_avahi_daemon.sh', check_exit=False)
		shutit.send('rm -f /usr/share/squid-deb-proxy-client/apt-avahi-discover')
		return True

	def start(self, shutit):
		# We seem to need to remove this so that our settings work. Since this is not a "real" machine, I think.
		shutit.send('rm -f /usr/share/squid-deb-proxy-client/apt-avahi-discover')
		shutit.send("""route -n | awk '/^0.0.0.0/ {print $2}' | tee /tmp/hostip""", check_exit=False)
		shutit.send("""echo "HEAD /" | nc `cat /tmp/hostip` """ + shutit.cfg['shutit.tk.squid_deb_proxy.squid_deb_proxy']['host_proxy_port'] + """ | grep squid-deb-proxy && (echo "Acquire::http::Proxy \\"http://$(cat /tmp/hostip):""" + shutit.cfg['shutit.tk.squid_deb_proxy.squid_deb_proxy']['host_proxy_port'] + """\\";" > /etc/apt/apt.conf.d/30proxy) && (echo "Acquire::http::Proxy::ppa.launchpad.net DIRECT;" >> /etc/apt/apt.conf.d/30proxy) || echo 'No squid-deb-proxy detected on docker host'""", check_exit=True)
		shutit.send('rm -f /tmp/hostip')
		shutit.send('/root/start_avahi_daemon.sh', check_exit=False)
		return True

	def stop(self, shutit):
		shutit.send('/root/stop_avahi_daemon.sh', check_exit=False)
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'host_proxy_port','8000')
		return True

def module():
	return squid_deb_proxy(
		'shutit.tk.squid_deb_proxy.squid_deb_proxy', 0.01,
		description='detects whether a squid deb proxy is available on the host and uses it',
		depends=['shutit.tk.setup']
	)

