
# Created from dockerfile: /tmp/a/Dockerfile
# Maintainer:              Joao Paulo Dubas &quot;joao.dubas@gmail.com&quot;
from shutit_module import ShutItModule

class orientdb(ShutItModule):

    def is_installed(self, shutit):
        return False

    def build(self, shutit):
        shutit.install('wget')
        shutit.install('tar')
        shutit.send('export ROOT=/opt/downloads')
        shutit.send('export ORIENT_URL=http://www.orientdb.org/portal/function/portal/download/unknown@unknown.com')
        shutit.send('export ORIENT_VERSION=orientdb-community-1.7.4')
        shutit.send('mkdir ${ROOT}')
        shutit.send('cd ${ROOT}')
        shutit.send('wget ${ORIENT_URL}/-/-/-/-/-/${ORIENT_VERSION}.tar.gz/false/false/linux')
        shutit.send('tar -xzf linux')
        shutit.send('ln -s ${ROOT}/${ORIENT_VERSION} ${ROOT}/orientdb')
        return True

    def finalize(self, shutit):
        shutit.send('rm -rf /opt/downloads/linux /var/lib/apt/lists/* /tmp/* /var/tmp/*')
        return True

    def test(self, shutit):
        return True

    def is_installed(self, shutit):
        return False

    def get_config(self, shutit):
        return True

def module():
        return orientdb(
                'shutit.tk.orientdb.orientdb', 782914092.00,
                depends=['shutit.tk.setup']
        )
