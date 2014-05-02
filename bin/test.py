import unittest
import shutit_main
import shutit_global
import util

# In order to dynamically create objects
class Bunch:
	def __init__(self, **kwds):
		self.__dict__.update(kwds)

# Updating multiple levels of a dict
import collections
def recupdate(d, u):
	for k, v in u.iteritems():
		if isinstance(v, collections.Mapping):
			r = recupdate(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d

class ShutItTestException(Exception):
	pass

class TestShutItDepChecking(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls._config_dict = shutit_global.config_dict
		cls._log = util.log
		cls._fail = util.fail
		def log(*args, **kwargs):
			pass
		def fail(*args, **kwargs):
			raise ShutItTestException("failed")
		util.log = log
		util.fail = fail
	@classmethod
	def tearDownClass(cls):
		util.log = cls._log
		util.fail = cls._fail

	def setUp(self):
		self.config_dict = shutit_global.config_dict = self._config_dict.copy()
		recupdate(self.config_dict, {
			'build': {
				'tutorial': False, 'debug': False, 'show_depgraph_only': False
			},
			'host': {'shutit_module_paths': 'dummy1:dummy2'}
		})

	def test_dep_exists_err(self):
		self.config_dict.update({
			'tk.shutit.test1': {'build': True, 'remove': False}
		})
		shutit_map = {
			'tk.shutit.test1': Bunch(
				module_id='tk.shutit.test1',
				run_order=1.1,
				depends_on=["tk.shutit.test0"])
		}
		shutit_id_list = ['tk.shutit.test1']
		self.assertRaises(
			ShutItTestException,
			shutit_main.check_deps,
			self.config_dict, shutit_map, shutit_id_list
		)

	def test_dep_build_err(self):
		self.config_dict.update({
			'tk.shutit.test1': {'build': False, 'build_ifneeded': False, 'remove': False},
			'tk.shutit.test2': {'build': True, 'remove': False}
		})
		shutit_map = {
			'tk.shutit.test2': Bunch(
				module_id='tk.shutit.test2',
				run_order=1.2,
				depends_on=["tk.shutit.test1"]),
			'tk.shutit.test1': Bunch(
				module_id='tk.shutit.test1',
				run_order=1.1,
				depends_on=[],
				is_installed=lambda c: False)
		}
		shutit_id_list = ['tk.shutit.test1', 'tk.shutit.test2']
		self.assertRaises(
			ShutItTestException,
			shutit_main.check_deps,
			self.config_dict, shutit_map, shutit_id_list
		)

	def test_dep_order_err(self):
		self.config_dict.update({
			'tk.shutit.test1': {'build': True, 'remove': False},
			'tk.shutit.test2': {'build': True, 'remove': False}
		})
		shutit_map = {
			'tk.shutit.test2': Bunch(
				module_id='tk.shutit.test2',
				run_order=1.2,
				depends_on=["tk.shutit.test1"]),
			'tk.shutit.test1': Bunch(
				module_id='tk.shutit.test1',
				run_order=1.9,
				depends_on=[])
		}
		shutit_id_list = ['tk.shutit.test1', 'tk.shutit.test2']
		self.assertRaises(
			ShutItTestException,
			shutit_main.check_deps,
			self.config_dict, shutit_map, shutit_id_list
		)

if __name__ == '__main__':
	unittest.main()
