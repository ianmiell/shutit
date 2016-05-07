from shutit_module import ShutItModule

import shutit_util

class test18(ShutItModule):

	def build(self, shutit):
		cfg = shutit.cfg
		shutit.send_file(shutit.build['build_db_dir'] + '/' + shutit.build['build_id'] + '/' + shutit.build['build_id'] + '.cfg', shutit_util.print_config(cfg))
		return True

def module():
	return test18(
		'shutit.test18.test18.test18', 349682177.00,
		description='',
		maintainer='',
		delivery_methods=['dockerfile','docker'],
		depends=['shutit.tk.setup']
	)

