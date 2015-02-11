
# Created from dockerfile: /tmp/a/Dockerfile
# Maintainer:              Joao Paulo Dubas &quot;joao.dubas@gmail.com&quot;
from shutit_module import ShutItModule

class spidermonkey(ShutItModule):

	def build(self, shutit):
		shutit.install('zip unzip libnspr4-dev wget')
		shutit.send('export SPIDER_ZIP=jsshell-linux-x86_64.zip')
		shutit.send('export SPIDER_ROOT=/opt/src/jsshell')
		shutit.send('mkdir -p ${SPIDER_ROOT}')
		shutit.send('cd ${SPIDER_ROOT}/../')
		shutit.send('wget http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/latest-trunk/${SPIDER_ZIP}')
		shutit.send('unzip ${SPIDER_ZIP} -d ${SPIDER_ROOT}')
		shutit.send('ln -s ${SPIDER_ROOT}/js /usr/local/bin')
		shutit.send('ln -s ${SPIDER_ROOT}/*.so /usr/local/share')
		return True

	def finalize(self, shutit):
		shutit.send('apt-get -y -qq --force-yes clean')
		shutit.send('export SPIDER_ZIP=jsshell-linux-x86_64.zip')
		shutit.send('export SPIDER_ROOT=/opt/src/jsshell')
		shutit.send('rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*')
		shutit.send('rm -rf ${SPIDER_ROOT}/../${SPIDER_ZIP}')
		return True

def module():
		return spidermonkey(
				'shutit.tk.spidermonkey.spidermonkey', 0.412415,
				depends=['shutit.tk.setup']
		)
