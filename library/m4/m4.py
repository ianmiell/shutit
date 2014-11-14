"""ShutIt module. See http://shutit.tk
In source, line 16 should be blank, within the build def. This doesn't matter except for test builds, so can be removed once in use.
"""

from shutit_module import ShutItModule


class m4(ShutItModule):


	def is_installed(self, shutit):
		return False


	def build(self, shutit):
		shutit.install('git')
		shutit.install('autoconf') # required
		shutit.send('pushd /opt')
		shutit.send('git clone git://git.sv.gnu.org/m4')
		shutit.send('pushd /opt/m4')
		shutit.send('./bootstrap')
		shutit.send('popd')
		shutit.send('popd')
		shutit.send('rm -rf /opt/m4')
		return True

	#def get_config(self, shutit):
	#	return True

	#def check_ready(self, shutit):
	#	return True
	
	#def start(self, shutit):
	#	return True

	#def stop(self, shutit):
	#	return True

	#def finalize(self, shutit):
	#	return True

	#def remove(self, shutit):
	#	return True

	#def test(self, shutit):
	#	return True

def module():
	return m4(
		'shutit.tk.m4.m4', 0.019,
		description='',
		maintainer='',
		depends=['shutit.tk.setup','shutit.tk.help2man.help2man','shutit.tk.xz.xz','shutit.tk.automake.automake','shutit.tk.libtool.libtool','shutit.tk.texinfo.texinfo','shutit.tk.gettext.gettext']
	)

