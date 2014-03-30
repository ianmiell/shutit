from shutit_module import ShutItModule
import util

# Useful links:

class mysql(ShutItModule):

	def check_ready(self,config_dict):
		return True

	def is_installed(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		res = util.file_exists(container_child,'/root/start_mysql.sh',config_dict['expect_prompts']['root_prompt'])
		return res

	def build(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'bash',config_dict['expect_prompts']['base_prompt'],check_exit=False)
		util.handle_login(container_child,config_dict,'mysql_tmp_prompt')
		expect = config_dict['expect_prompts']['mysql_tmp_prompt']
		root_pass = config_dict['com.ian.miell.mysql.mysql']['root_password']
		# From the perfmon doc set the mysql root password non-interactively
		util.send_and_expect(container_child,"""debconf-set-selections <<< 'mysql-server mysql-server/root_password password {0}'""".format(root_pass),expect,record_command=False)
		util.send_and_expect(container_child,"""sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password {0}'""".format(root_pass),expect,record_command=False)
		util.send_and_expect(container_child,'apt-get install -qq -y mysql-server libmysqlclient-dev',expect)
		util.send_and_expect(container_child,'mysqld &',expect)
		util.send_and_expect(container_child,'sleep 2',expect)
		util.send_and_expect(container_child,'mysql_install_db --user=mysql --basedir=/usr --datadir=/var/mysql/database',expect)
		# http://stackoverflow.com/questions/15663001/remote-connections-mysql-ubuntu
                util.send_and_expect(container_child,"perl -p -i -e 's/^bind.*/bind-address = 0.0.0.0/' /etc/mysql/my.cnf",expect)
		res = util.send_and_expect(container_child,"""echo "create user '""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """'@'localhost' identified by '""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """'" | mysql -p """,['assword',expect],check_exit=False)
		if res == 0:
			util.send_and_expect(container_child,root_pass,expect)
		res = util.send_and_expect(container_child,"""echo "create user '""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """'@'%' identified by '""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """'" | mysql -p """,['assword',expect],check_exit=False)
		if res == 0:
			util.send_and_expect(container_child,root_pass,expect)
		res = util.send_and_expect(container_child,"""echo "grant all privileges on *.* to '""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """'@'localhost';" | mysql -p""",['assword',expect],check_exit=False)
		if res == 0:
			util.send_and_expect(container_child,root_pass,expect)
		res = util.send_and_expect(container_child,"""echo "grant all privileges on *.* to '""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """'@'%';" | mysql -p""",['assword',expect],check_exit=False)
		if res == 0:
			util.send_and_expect(container_child,root_pass,expect)
		res = util.send_and_expect(container_child,"""echo "set password for """ + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """@'localhost'  = password('""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user_password'] + """')" | mysql -p""",['assword',expect],check_exit=False,record_command=False)
		if res == 0:
			util.send_and_expect(container_child,root_pass,expect)
		res = util.send_and_expect(container_child,"""echo "set password for """ + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + """@'%'  = password('""" + config_dict['com.ian.miell.mysql.mysql']['mysql_user_password'] + """')" | mysql -p""",['assword',expect],check_exit=False,record_command=False)
		if res == 0:
			util.send_and_expect(container_child,root_pass,expect)
		res = util.add_line_to_file(container_child,'nohup mysqld &','/root/start_mysql.sh',expect)
		if res:
			util.add_line_to_file(container_child,'echo "Starting mysqld, sleeping"','/root/start_mysql.sh',expect,force=True)
			util.add_line_to_file(container_child,'sleep 2','/root/start_mysql.sh',expect,force=True)
		res = util.add_line_to_file(container_child,'# mysql','/root/stop_mysql.sh',expect)
		if res:
			util.add_line_to_file(container_child,'# mysql','/root/stop_mysql.sh',expect,truncate=True)
			util.add_line_to_file(container_child,'echo "Stopping mysql"','/root/stop_mysql.sh',expect,force=True)
			util.send_and_expect(container_child,"""cat >> /root/stop_mysql.sh <<< "if [ x\`ps -ef | grep mysqld$ | grep -v grep | awk '{print \$2}' | wc -l\` = 'x0' ]" """,expect)
			util.add_line_to_file(container_child,'then','/root/stop_mysql.sh',expect,force=True)
			util.add_line_to_file(container_child,'/bin/true','/root/stop_mysql.sh',expect,force=True)
			util.add_line_to_file(container_child,'else','/root/stop_mysql.sh',expect,force=True)
			util.send_and_expect(container_child,"""cat >> /root/stop_mysql.sh <<< "ps -ef | grep mysqld$ | awk '{print \$2}' | sed 's/\([0-9]*\)/ kill -9 \\1/' | sh" """,expect)
			util.add_line_to_file(container_child,'echo "sleeping 2"','/root/stop_mysql.sh',expect,force=True)
			util.add_line_to_file(container_child,'sleep 2','/root/stop_mysql.sh',expect,force=True)
			util.add_line_to_file(container_child,'fi','/root/stop_mysql.sh',expect,force=True)
		util.send_and_expect(container_child,'chmod +x /root/start_mysql.sh',expect)
		util.send_and_expect(container_child,'chmod +x /root/stop_mysql.sh',expect)
		util.send_and_expect(container_child,'/root/stop_mysql.sh',expect)
		util.send_and_expect(container_child,'/root/start_mysql.sh',expect)
		util.handle_revert_prompt(container_child,config_dict['expect_prompts']['base_prompt'],'mysql_tmp_prompt')
		util.send_and_expect(container_child,'exit',config_dict['expect_prompts']['root_prompt'])
		return True

	def start(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/start_mysql.sh',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def stop(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'/root/stop_mysql.sh',config_dict['expect_prompts']['root_prompt'],check_exit=False)
		return True


	def cleanup(self,config_dict):
		return True

	def remove(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'apt-get -qq -y purge mysql-server libmysqlclient-dev mysql-common',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'/root/stop_mysql.sh',config_dict['expect_prompts']['root_prompt'])
		#http://stackoverflow.com/questions/10853004/removing-mysql-5-5-completely et al
		util.send_and_expect(container_child,'rm -rf /var/lib/mysql',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'rm -rf /etc/mysql',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'deluser mysql',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'apt-get -qq -y autoremove',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'apt-get -qq -y autoclean',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'find / -iname \'mysql*\'',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'rm /root/start_mysql.sh',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'rm /root/stop_mysql.sh',config_dict['expect_prompts']['root_prompt'])
		return True

	def test(self,config_dict):
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'mysql -u' + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + ' -p' + config_dict['com.ian.miell.mysql.mysql']['mysql_user_password'],'mysql>',check_exit=False,record_command=False)
		util.send_and_expect(container_child,'\q',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'mysql -u' + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + ' -hlocalhost -p' + config_dict['com.ian.miell.mysql.mysql']['mysql_user_password'],'mysql>',check_exit=False,record_command=False)
		util.send_and_expect(container_child,'\q',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'mysql -u' + config_dict['com.ian.miell.mysql.mysql']['mysql_user'] + ' -hlocalhost -p' + config_dict['com.ian.miell.mysql.mysql']['mysql_user_password'],'mysql>',check_exit=False,record_command=False)
		util.send_and_expect(container_child,'\q',config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'mysql -uroot -p' + config_dict['com.ian.miell.mysql.mysql']['root_password'],'mysql>',check_exit=False,record_command=False)
		util.send_and_expect(container_child,'\q',config_dict['expect_prompts']['root_prompt'])
		return True

	def finalize(self,config_dict):
		return True

	def get_config(self,config_dict):
		cp = config_dict['config_parser']
		config_dict['com.ian.miell.mysql.mysql']['mysql_user']               = cp.get('com.ian.miell.mysql.mysql','mysql_user')
		config_dict['com.ian.miell.mysql.mysql']['mysql_user_password']      = cp.get('com.ian.miell.mysql.mysql','mysql_user_password')
		config_dict['com.ian.miell.mysql.mysql']['root_password']            = cp.get('com.ian.miell.mysql.mysql','root_password')
		return True

if not util.module_exists('com.ian.miell.mysql.mysql'):
	obj = mysql('com.ian.miell.mysql.mysql',1037228939.0)
	obj.add_dependency('com.ian.miell.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(mysql)

