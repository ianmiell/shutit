import shutit_global
import shutit_pexpect
import shutit_util
import shutit_setup


def create_bash_session():
	shutit = shutit_global.shutit
	shutit_util.parse_args()
	shutit_util.load_configs()
	shutit_setup.setup_host_child_environment(shutit)
	return shutit


def create_docker_session():
	shutit = shutit_global.shutit
	shutit_util.parse_args()
	shutit_util.load_configs()
	target_child = shutit_setup.conn_docker_start_container(shutit,'target_child')
	shutit_setup.setup_host_child_environment(shutit)
	shutit_setup.setup_target_child_environment(shutit, target_child)
	return shutit

if __name__ == '__main__':
	shutit = create_bash_session()
	shutit.send('hostname')
	shutit = create_docker_session()
	shutit.send('hostname')
