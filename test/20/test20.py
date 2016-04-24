from shutit_module import ShutItModule
import time

class test20(ShutItModule):

	def build(self, shutit):
		d = '/tmp/git-rebase-tutorial-test'
		shutit.send('rm -rf ' + d)
		shutit.send('mkdir -p ' + d)
		shutit.send('cd ' + d)
		shutit.send('git clone https://github.com/ianmiell/git-rebase-tutorial && cd git-rebase-tutorial')
		shutit.send('./run.sh',expect='fixterm')
		time.sleep(1)
		shutit.send('git init',expect='rebase_tutorial')
		shutit.send(r'',expect='fixterm')
		shutit.logout()
		shutit.send('rm -rf ' + d)
		return True

def module():
	return test20(
		'tk.shutit.test20', 1845506479.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup']
	)
