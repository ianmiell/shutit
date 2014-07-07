
# Created from dockerfile: /space/git/dockerfiles_repos/ahazem/android-dockerfile/Dockerfile
from shutit_module import ShutItModule

class android_dev(ShutItModule):

        def is_installed(self,shutit):
                return False

        def build(self,shutit):
		shutit.send('echo "debconf shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections')
		shutit.send('echo "debconf shared/accepted-oracle-license-v1-1 seen true" | debconf-set-selections')
		shutit.send('apt-get -y install python-software-properties bzip2')
		if shutit.send('add-apt-repository ppa:webupd8team/java',expect=['to continue',shutit.cfg['expect_prompts']['root_prompt']]) == 0:
			shutit.send('')
		shutit.send('echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list')
		shutit.send('apt-get update')
		shutit.send('apt-get -y install oracle-java6-installer')
		shutit.send('apt-get install libfuse2')
		shutit.send('cd /tmp ; apt-get download fuse')
		shutit.send('cd /tmp ; dpkg-deb -x fuse_* .')
		shutit.send('cd /tmp ; dpkg-deb -e fuse_*')
		shutit.send('cd /tmp ; rm fuse_*.deb')
		shutit.send('cd /tmp ; echo -en \'#!/bin/bash\nexit 0\n\' > DEBIAN/postinst')
		shutit.send('cd /tmp ; dpkg-deb -b . /fuse.deb')
		shutit.send('cd /tmp ; dpkg -i /fuse.deb')
		shutit.send('apt-get -y install ia32-libs-multiarch')
		shutit.send('wget http://dl.google.com/android/android-sdk_r22.3-linux.tgz')
		shutit.send('tar -xvzf android-sdk_r22.3-linux.tgz')
		shutit.send('mv android-sdk-linux /usr/local/android-sdk')
		shutit.send('wget http://dl.google.com/android/ndk/android-ndk-r9c-linux-x86_64.tar.bz2')
		shutit.send('tar -xvjf android-ndk-r9c-linux-x86_64.tar.bz2')
		shutit.send('mv android-ndk-r9c /usr/local/android-ndk')
		shutit.send('wget http://archive.apache.org/dist/ant/binaries/apache-ant-1.8.4-bin.tar.gz')
		shutit.send('tar -xvzf apache-ant-1.8.4-bin.tar.gz')
		shutit.send('mv apache-ant-1.8.4 /usr/local/apache-ant')
		shutit.send('export ANDROID_HOME=/usr/local/android-sdk')
		shutit.send('export PATH=$PATH:$ANDROID_HOME/tools')
		shutit.send('export PATH=$PATH:$ANDROID_HOME/platform-tools')
		shutit.send('export ANT_HOME=/usr/local/apache-ant')
		shutit.send('export PATH=$PATH:$ANT_HOME/bin')
		shutit.send('export JAVA_HOME=/usr/lib/jvm/java-6-oracle')
		shutit.send('cd /; rm android-sdk_r22.3-linux.tgz && rm android-ndk-r9c-linux-x86_64.tar.bz2 && rm apache-ant-1.8.4-bin.tar.gz')
		shutit.send('echo "y" | android update sdk --no-ui --force --filter platform-tools,android-19,build-tools-19.0.1,sysimg-19')
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
        return android_dev(
                'shutit.tk.android_dev.android_dev', 0.1567365,
                depends=['shutit.tk.setup']
        )
