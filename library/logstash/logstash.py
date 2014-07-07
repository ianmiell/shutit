
# Created from dockerfile: /space/git/dockerfiles_repos/logstash-dockerfile/Dockerfile
from shutit_module import ShutItModule

class logstash(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('export DEBIAN_FRONTEND=noninteractive')
		shutit.send('export LUMBERJACK_TAG=MYTAG')
		shutit.send('export ELASTICWORKERS=1')
		shutit.send('apt-get update')
		shutit.send('apt-get install -y wget openjdk-6-jre')
		shutit.send('wget https://download.elasticsearch.org/logstash/logstash/logstash-1.3.3-flatjar.jar -O /opt/logstash.jar --no-check-certificate 2>/dev/null')
		shutit.send_host_file('/usr/local/bin/run.sh','context/run.sh')
		shutit.send('chmod +x /usr/local/bin/run.sh')
		shutit.send('mkdir /opt/certs/')
		shutit.send_host_file('/opt/certs/logstash-forwarder.crt','context/certs/logstash-forwarder.crt')
		shutit.send_host_file('/opt/certs/logstash-forwarder.key','context/certs/logstash-forwarder.key')
		shutit.send_host_file('/opt/collectd-types.db','context/collectd-types.db')
                return True

	def finalize(self,shutit):
		return True

	def test(self,shutit):
		return True

	def is_installed(self,shutit):
		return False

	def get_config(self,shutit):
		return True

def module():
        return logstash(
                'shutit.tk.logstash.logstash', 0.15645626,
                depends=['shutit.tk.setup']
        )
