import shutit_global
import shutit_pexpect
import shutit_util
import shutit_setup
 
 
def create_bash_session():
	shutit = shutit_global.shutit
	shutit_util.parse_args()
	shutit_util.load_configs()
	shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession('target_child','/bin/bash')
	target_child = shutit_pexpect_session.pexpect_child
	shutit.set_default_shutit_pexpect_session(shutit_pexpect_session)                                                                                 
	shutit.set_default_shutit_pexpect_session_expect(shutit.expect_prompts['base_prompt'])                                                            
	prefix = 'ORIGIN_ENV'                                                                                                                             
	shutit_pexpect_session.setup_prompt('origin_prompt', prefix=prefix)                                                                               
	shutit_pexpect_session.login_stack_append(prefix)                                                                                                 
	shutit_pexpect_session = shutit.get_shutit_pexpect_session_from_id('target_child')                                                               
	shutit_pexpect_session.pexpect_child = target_child                                                                                               
	shutit.set_default_shutit_pexpect_session_expect(shutit.expect_prompts['base_prompt'])                                                            
	shutit.set_default_shutit_pexpect_session(shutit_pexpect_session)                                                                                 
	shutit_pexpect_session.setup_prompt(prefix,prefix=prefix)                                                                                         
	shutit_pexpect_session.login_stack_append(prefix)     
	return shutit


def create_docker_session():
	shutit = shutit_global.shutit
	shutit_util.parse_args()
	shutit_util.load_configs()
	shutit_pexpect_session = shutit_pexpect.ShutItPexpectSession('target_child','/bin/bash')
	target_child = shutit_pexpect_session.pexpect_child
	
	shutit.set_default_shutit_pexpect_session(shutit_pexpect_session)                                                                                 
	shutit.set_default_shutit_pexpect_session_expect(shutit.expect_prompts['base_prompt'])                                                            
	prefix = 'ORIGIN_ENV'                                                                                                                             
	shutit_pexpect_session.setup_prompt('origin_prompt', prefix=prefix)                                                                               
	shutit_pexpect_session.login_stack_append(prefix)                                                                                                 
	
	target_child = shutit_setup.conn_docker_start_container(shutit,'ORIGIN')
	shutit_pexpect_session = shutit.get_shutit_pexpect_session_from_id('target_child')
	shutit_pexpect_session.pexpect_child = target_child
	shutit.set_default_shutit_pexpect_session_expect(shutit.expect_prompts['base_prompt'])
	shutit.set_default_shutit_pexpect_session(shutit_pexpect_session)
	shutit_pexpect_session.setup_prompt(prefix,prefix=prefix)
	shutit_pexpect_session.login_stack_append(prefix)
	return shutit


if __name__ == '__main__':
	create_bash_session()
	create_docker_session()
