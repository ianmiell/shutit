#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

from shutit_module import ShutItModule

#cf http://www.spinellis.gr/blog/20130619/

class git_server(ShutItModule):

	def build(self, shutit):
		shutit.install('apache2')
		shutit.install('git-core')
		shutit.install('vim')
		shutit.install('telnet')
		shutit.send('mkdir -p /var/cache/git')
		shutit.send('git daemon --base-path=/var/cache/git --detach --syslog --export-all')
		# TODO: turn into start/stop script
		shutit.add_to_bashrc('git daemon --base-path=/var/cache/git --detach --syslog --export-all')
		return True

	def start(self, shutit):
		# TODO
		return True

	def stop(self, shutit):
		# TODO
		return True

def module():
	return git_server(
		'shutit.tk.git_server.git_server', 0.316,
		description='minimal git server',
		depends=['shutit.tk.setup']
	)

