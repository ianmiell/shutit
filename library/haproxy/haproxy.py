
# Created from dockerfile: ./Dockerfile
# Maintainer:              Alan Boudreault "boudreault.alan@gmail.com"

# See also http://oskarhane.com/haproxy-as-a-static-reverse-proxy-for-docker-containers/
from shutit_module import ShutItModule

class haproxy(ShutItModule):

	def build(self, shutit):
		shutit.send('export HAPROXY_VERSION=1.5-dev22')
		shutit.send('export HAPROXY=haproxy-$HAPROXY_VERSION')
		shutit.send('export TMP_DIR=/tmp')
		shutit.send('export SSL_SUBJ=/C=CA/ST=QC/L=Saguenay/O=Dis/CN=alanb.ca')
		# Compile and Install haproxy 1.5
		shutit.send('apt-get install -y wget build-essential libssl-dev openssl')
		shutit.send('wget -O $TMP_DIR/$HAPROXY.tar.gz http://haproxy.1wt.eu/download/1.5/src/devel/$HAPROXY.tar.gz')
		shutit.send('cd $TMP_DIR ; tar -xzf $HAPROXY.tar.gz')
		shutit.send('make -C $TMP_DIR/$HAPROXY TARGET=generic USE_OPENSSL=1')
		shutit.send('make -C $TMP_DIR/$HAPROXY install')
		# Create haproxy user
		shutit.send('addgroup --system haproxy')
		shutit.send('adduser --system --no-create-home --ingroup haproxy haproxy')
		# Generate SSL certificate for https
		shutit.send('openssl req -new -newkey rsa:2048 -days 1825 -nodes -x509 -subj $SSL_SUBJ -keyout server.key -out server.crt')
		shutit.send('cat server.crt server.key > server.pem')
		shutit.send('mv server.* /etc/ssl/certs/')
		shutit.send('chmod o-r /etc/ssl/certs/*')
		shutit.send('chown haproxy.haproxy /etc/ssl/certs/server.pem')
		shutit.send('mkdir /etc/haproxy')
		shutit.send_host_file('/etc/haproxy/haproxy.conf', 'context/./haproxy.conf')
		return True

def module():
		return haproxy(
				'shutit.tk.haproxy.haproxy', 0.113621462,
		description='',
				depends=['shutit.tk.setup']
		)
