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
		cls.shutit = shutit_global.shutit
		cls._cfg = shutit_global.shutit.cfg
		cls._shutit_map = shutit_global.shutit.shutit_map
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
		self.shutit.cfg = self._cfg.copy()
		self.shutit.shutit_map = self._shutit_map.copy()
		recupdate(self.shutit.cfg, {
			'build': {
				'tutorial': False, 'debug': False, 'show_depgraph_only': False
			},
			'host': {'shutit_module_paths': 'dummy1:dummy2'}
		})

	def test_dep_exists_err(self):
		self.shutit.cfg.update({
			'tk.shutit.test1': {'build': True, 'remove': False}
		})
		self.shutit.shutit_map = {
			'tk.shutit.test1': Bunch(
				module_id='tk.shutit.test1',
				run_order=1.1,
				depends_on=["tk.shutit.test0"])
		}
		errs = shutit_main.check_deps(self.shutit)
		self.assertEqual(len(errs), 1)

	def test_dep_build_err(self):
		self.shutit.cfg.update({
			'tk.shutit.test1': {'build': False, 'build_ifneeded': False, 'remove': False},
			'tk.shutit.test2': {'build': True, 'remove': False}
		})
		self.shutit.shutit_map = {
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
		errs = shutit_main.check_deps(self.shutit)
		self.assertEqual(len(errs), 1)

	def test_dep_order_err(self):
		self.shutit.cfg.update({
			'tk.shutit.test1': {'build': True, 'remove': False},
			'tk.shutit.test2': {'build': True, 'remove': False}
		})
		self.shutit.shutit_map = {
			'tk.shutit.test2': Bunch(
				module_id='tk.shutit.test2',
				run_order=1.2,
				depends_on=["tk.shutit.test1"]),
			'tk.shutit.test1': Bunch(
				module_id='tk.shutit.test1',
				run_order=1.9,
				depends_on=[])
		}
		errs = shutit_main.check_deps(self.shutit)
		self.assertEqual(len(errs), 1)

	def test_dep_resolution(self):
		self.shutit.cfg.update({
			'tk.shutit.test1': {'build': False, 'build_ifneeded': True, 'remove': False},
			'tk.shutit.test2': {'build': False, 'build_ifneeded': True, 'remove': False},
			'tk.shutit.test3': {'build': True, 'remove': False}
		})
		self.shutit.shutit_map = {
			'tk.shutit.test3': Bunch(
				module_id='tk.shutit.test3',
				run_order=1.3,
				depends_on=["tk.shutit.test2"]),
			'tk.shutit.test2': Bunch(
				module_id='tk.shutit.test2',
				run_order=1.2,
				depends_on=["tk.shutit.test1"]),
			'tk.shutit.test1': Bunch(
				module_id='tk.shutit.test1',
				run_order=1.1,
				depends_on=[])
		}
		shutit_main.check_deps(self.shutit)
		assert all([self.shutit.cfg[mod_id]['build'] for mod_id in self.shutit.shutit_map])

if __name__ == '__main__':
	unittest.main()
