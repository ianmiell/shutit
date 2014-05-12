#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


from shutit_module import ShutItModule
import util

class mysql(ShutItModule):

	def is_installed(self,shutit):
		return shutit.file_exists('/root/start_mysql.sh')

	def build(self,shutit):
		container_child = util.get_pexpect_child('container_child')
		shutit.send_and_expect('bash',check_exit=False)
		util.handle_login(container_child,shutit.cfg,'mysql_tmp_prompt')
		shutit.set_default_expect(shutit.cfg['expect_prompts']['mysql_tmp_prompt'])
		root_pass = shutit.cfg['shutit.tk.mysql.mysql']['root_password']
		shutit.send_and_expect("apt-get update", record_command=False)
		shutit.send_and_expect("""debconf-set-selections <<< 'mysql-server mysql-server/root_password password {0}'""".format(root_pass),record_command=False)
		shutit.send_and_expect("""sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password {0}'""".format(root_pass),record_command=False)
		shutit.install('mysql-common')
		shutit.install('mysql-server')
		shutit.install('libmysqlclient-dev')
		shutit.send_and_expect('mysqld &')
		shutit.send_and_expect('sleep 2')
		shutit.send_and_expect('mysql_install_db --user=mysql --basedir=/usr --datadir=/var/mysql/database')
		# http://stackoverflow.com/questions/15663001/remote-connections-mysql-ubuntu
		shutit.send_and_expect("perl -p -i -e 's/^bind.*/bind-address = 0.0.0.0/' /etc/mysql/my.cnf")
		mysql_user = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']
		res = shutit.send_and_expect('mysql -p',['assword','mysql>'],check_exit=False)
		if res == 0:
			shutit.send_and_expect(root_pass,'mysql>',check_exit=False)
		shutit.send_and_expect("create user '" + mysql_user + "'@'localhost' identified by '" + mysql_user + "';",'mysql>',check_exit=False)
		shutit.send_and_expect("create user '" + mysql_user + "'@'%' identified by '" + mysql_user + "';",'mysql>',check_exit=False)
		shutit.send_and_expect("grant all privileges on *.* to '" + mysql_user + "'@'localhost';",'mysql>',check_exit=False)
		shutit.send_and_expect("grant all privileges on *.* to '" + mysql_user + "'@'%';",'mysql>',check_exit=False)
		shutit.send_and_expect("set password for " + mysql_user + "@'localhost' = password('" + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + "');",'mysql>',check_exit=False,record_command=False)
		shutit.send_and_expect("set password for " + mysql_user + "@'%' = password('" + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + "');",'mysql>',check_exit=False,record_command=False)
		shutit.send_and_expect('\q')
		res = shutit.add_line_to_file('nohup mysqld &','/root/start_mysql.sh')
		if res:
			shutit.add_line_to_file("""echo Starting mysqld, sleeping""",'/root/start_mysql.sh',force=True)
			shutit.add_line_to_file('sleep 2','/root/start_mysql.sh',force=True)
		res = shutit.add_line_to_file('# mysql','/root/stop_mysql.sh')
		if res:
			shutit.add_line_to_file('# mysql','/root/stop_mysql.sh',truncate=True)
			shutit.add_line_to_file("""echo Stopping mysql""",'/root/stop_mysql.sh',force=True)
			shutit.send_and_expect("""cat >> /root/stop_mysql.sh <<< "if [ x\`ps -ef | grep mysqld$ | grep -v grep | awk '{print \$2}' | wc -l\` = 'x0' ]" """)
			shutit.add_line_to_file('then','/root/stop_mysql.sh',force=True)
			shutit.add_line_to_file('/bin/true','/root/stop_mysql.sh',force=True)
			shutit.add_line_to_file('else','/root/stop_mysql.sh',force=True)
			shutit.send_and_expect("""cat >> /root/stop_mysql.sh <<< "ps -ef | grep mysqld$ | awk '{print \$2}' | sed 's/\([0-9]*\)/ kill -9 \\1/' | sh" """)
			shutit.add_line_to_file("""echo sleeping 2""",'/root/stop_mysql.sh',force=True)
			shutit.add_line_to_file('sleep 2','/root/stop_mysql.sh',force=True)
			shutit.add_line_to_file('fi','/root/stop_mysql.sh',force=True)
		shutit.send_and_expect('chmod +x /root/start_mysql.sh')
		shutit.send_and_expect('chmod +x /root/stop_mysql.sh')
		shutit.send_and_expect('/root/stop_mysql.sh')
		shutit.send_and_expect('/root/start_mysql.sh')
		util.handle_revert_prompt(container_child,shutit.cfg['expect_prompts']['base_prompt'],'mysql_tmp_prompt')
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.send_and_expect('exit')
		return True

	def start(self,shutit):
		shutit.send_and_expect('/root/start_mysql.sh',shutit.cfg['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def stop(self,shutit):
		shutit.send_and_expect('/root/stop_mysql.sh',shutit.cfg['expect_prompts']['root_prompt'],check_exit=False)
		return True

	def remove(self,shutit):
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		shutit.remove('libmysqlclient-dev')
		shutit.remove('mysql-common')
		shutit.send_and_expect('/root/stop_mysql.sh')
		#http://stackoverflow.com/questions/10853004/removing-mysql-5-5-completely et al
		shutit.send_and_expect('rm -rf /var/lib/mysql')
		shutit.send_and_expect('rm -rf /etc/mysql')
		shutit.send_and_expect('deluser mysql',check_exit=False)
		install_type = shutit.cfg['container']['install_type']
		if install_type == 'apt':
			shutit.send_and_expect('apt-get -qq -y autoremove')
			shutit.send_and_expect('apt-get -qq -y autoclean')
		shutit.send_and_expect('find / -iname \'mysql*\' | xargs rm -rf')
		shutit.send_and_expect('rm /root/start_mysql.sh')
		shutit.send_and_expect('rm /root/stop_mysql.sh')
		return True

	def test(self,shutit):
		shutit.set_default_expect(shutit.cfg['expect_prompts']['root_prompt'])
		mysql_user = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']
		mysql_password = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password']
		root_password = shutit.cfg['shutit.tk.mysql.mysql']['root_password']
		shutit.send_and_expect('mysql -u' + mysql_user + ' -p' + mysql_password,'mysql>',check_exit=False,record_command=False)
		shutit.send_and_expect('\q')
		shutit.send_and_expect('mysql -u' + mysql_user + ' -hlocalhost -p' + mysql_password,'mysql>',check_exit=False,record_command=False)
		shutit.send_and_expect('\q')
		shutit.send_and_expect('mysql -u' + mysql_user + ' -hlocalhost -p' + mysql_password,'mysql>',check_exit=False,record_command=False)
		shutit.send_and_expect('\q')
		shutit.send_and_expect('mysql -uroot -p' + root_password,'mysql>',check_exit=False,record_command=False)
		shutit.send_and_expect('\q')
		return True

	def get_config(self,shutit):
		cp = shutit.cfg['config_parser']
		shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']          = cp.get('shutit.tk.mysql.mysql','mysql_user')
		shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] = cp.get('shutit.tk.mysql.mysql','mysql_user_password')
		shutit.cfg['shutit.tk.mysql.mysql']['root_password']       = cp.get('shutit.tk.mysql.mysql','root_password')
		return True

if not util.module_exists('shutit.tk.mysql.mysql'):
	obj = mysql('shutit.tk.mysql.mysql',0.318,'ShutIt MySql module. Sets up a user/password and the root password.')
	obj.add_dependency('shutit.tk.setup')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(mysql)

