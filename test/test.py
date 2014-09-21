import unittest
import shutit_main
import shutit_global

# In order to dynamically create objects
class Bunch:
	"""TODO
	"""
	def __init__(self, **kwds):
		self.__dict__.update(kwds)

# Updating multiple levels of a dict
import collections
def recupdate(d, u):
	"""TODO
	"""
	for k, v in u.iteritems():
		if isinstance(v, collections.Mapping):
			r = recupdate(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d

class ShutItTestException(Exception):
	"""TODO
	"""
	pass

class TestShutItDepChecking(unittest.TestCase):
	"""TODO
	"""

	def setUp(self):
		"""TODO
		"""
		self.shutit = shutit_global.init()
		def noop(*args, **kwargs):
			pass
		def fail(*args, **kwargs):
			raise ShutItTestException("failed")
		self.shutit.log = noop
		self.shutit.fail = fail
		self.shutit.get_default_child = noop
		recupdate(self.shutit.cfg, {
			'build': {
				'tutorial': False, 'debug': False, 'show_depgraph_only': False,
				'interactive': 0
			},
			'host': {'shutit_module_path': 'dummy1:dummy2'}
		})

	def test_dep_exists_err(self):
		"""TODO
		"""
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
		self.assertEqual(len(errs[0]), 1)

	def test_dep_build_err(self):
		"""TODO
		"""
		self.shutit.cfg.update({
			'tk.shutit.test1': {'build': False, 'shutit.core.module.build_ifneeded': False, 'remove': False},
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
		self.assertEqual(len(errs[0]), 1)

	def test_dep_order_err(self):
		"""TODO
		"""
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
		self.assertEqual(len(errs[0]), 1)

	def test_dep_resolution(self):
		"""TODO
		"""
		self.shutit.cfg.update({
			'tk.shutit.test1': {'build': False, 'shutit.core.module.build_ifneeded': True, 'remove': False},
			'tk.shutit.test2': {'build': False, 'shutit.core.module.build_ifneeded': True, 'remove': False},
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
		errs = shutit_main.check_deps(self.shutit)
		self.assertEqual(len(errs), 0)
		assert all([self.shutit.cfg[mod_id]['build'] for mod_id in self.shutit.shutit_map])

if __name__ == '__main__':
	unittest.main()
