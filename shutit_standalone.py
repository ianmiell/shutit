import shutit_global
import shutit_util
import shutit_setup


def create_bash_session(shutit=None):
	shutit = shutit or shutit_global.shutit
	shutit_util.parse_args()
	shutit_util.load_configs()
	shutit_setup.setup_host_child_environment(shutit)
	return shutit


def create_docker_session(shutit=None, docker_image=None, rm=None, loglevel='INFO'):
	shutit = shutit or shutit_global.shutit
	shutit_util.parse_args(set_loglevel=loglevel)
	# Set the configuration up appropriately using overrides.
	if docker_image:	
		shutit.build['config_overrides'].append(['build','base_image',docker_image])
	if rm:
		shutit.target['rm'] = True
	# Now 'load' the configs
	shutit_util.load_configs()
	target_child = shutit_setup.conn_docker_start_container(shutit,'target_child')
	shutit_setup.setup_host_child_environment(shutit)
	shutit_setup.setup_target_child_environment(shutit, target_child)
	return shutit


if __name__ == '__main__':
	shutit = create_docker_session(docker_image='ubuntu:16.04',rm=False, loglevel='DEBUG')
	#shutit.send('yum update')
	shutit.send('hostname')
	shutit.install('git')
	shutit.send('git clone https://github.com/ianmiell/shutitfile')
	shutit.send('grep asdasdasd shutitfile/README.md')
	shutit = create_bash_session()
	shutit.send('hostname')
