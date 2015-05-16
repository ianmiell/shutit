from shutit_module import ShutItModule

class mysql(ShutItModule):

	def build(self, shutit):
		root_pass = shutit.cfg['shutit.tk.mysql.mysql']['root_password']
		shutit.install('sudo')
		if shutit.get_current_environment()['install_type'] == 'apt':
			shutit.send("""debconf-set-selections << 'END'
mysql-server mysql-server/root_password password {0}
END""".format(root_pass), echo=False)
			shutit.send("""debconf-set-selections << 'END'
mysql-server mysql-server/root_password_again password {0}
END""".format(root_pass), echo=False)
			shutit.install('mysql-common')
			shutit.install('libmysqlclient-dev')
		else:
			shutit.install('mysql')
		shutit.install('mysql-server')
		shutit.send('mysqld &')
		shutit.send('sleep 2')
		shutit.send('mysql_install_db --user=mysql --basedir=/usr --datadir=/var/mysql/database')
		#http://stackoverflow.com/questions/10853004/removing-mysql-5-5-completely et al
		shutit.send("perl -p -i -e 's/^bind.*/bind-address = 0.0.0.0/' /etc/mysql/my.cnf")
		mysql_user = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']
		res = shutit.send('mysql -p', expect=['assword', 'mysql>'])
		if res == 0:
			shutit.send(root_pass, expect='mysql>', echo=False)
		shutit.send("create user '" + mysql_user + "'@'localhost' identified by '" + mysql_user + "';", expect='mysql>')
		shutit.send("create user '" + mysql_user + "'@'%' identified by '" + mysql_user + "';", expect='mysql>')
		shutit.send("grant all privileges on *.* to '" + mysql_user + "'@'localhost';", expect='mysql>')
		shutit.send("grant all privileges on *.* to '" + mysql_user + "'@'%';", expect='mysql>')
		shutit.send("set password for " + mysql_user + "@'localhost' = password('" + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + "');", expect='mysql>', echo=False)
		shutit.send("set password for " + mysql_user + "@'%' = password('" + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + "');", expect='mysql>', echo=False)
		shutit.send(r'\q')
		shutit.send_file('/root/start_mysql.sh', '''
			nohup mysqld &
			echo Starting mysqld, sleeping
			sleep 2''')
		shutit.send_file('/root/stop_mysql.sh', r'''
			# mysql
			echo Stopping mysql
			if [ x$(ps -ef | grep mysqld$ | grep -v grep | awk '{print $2}' | wc -l) = 'x0' ]
			then
				/bin/true
			else
				ps -ef | grep mysqld$ | awk '{print $2}' | sed 's/\([0-9]*\)/ kill -9 \1/' | sh
				echo sleeping 2
				sleep 2
			fi''')
		shutit.send('chmod +x /root/start_mysql.sh')
		shutit.send('chmod +x /root/stop_mysql.sh')
		shutit.send('/root/stop_mysql.sh')
		shutit.send('/root/start_mysql.sh')
		return True

	def start(self, shutit):
		shutit.send('/root/start_mysql.sh', check_exit=False)
		return True

	def stop(self, shutit):
		shutit.send('/root/stop_mysql.sh', check_exit=False)
		return True

	def remove(self, shutit):
		shutit.remove('libmysqlclient-dev')
		shutit.remove('mysql-common')
		shutit.send('/root/stop_mysql.sh')
		shutit.send('rm -rf /var/lib/mysql')
		shutit.send('rm -rf /etc/mysql')
		shutit.send('deluser mysql', check_exit=False)
		install_type = shutit.get_current_environment()['install_type']
		if install_type == 'apt':
			shutit.send('apt-get -qq -y autoremove')
			shutit.send('apt-get -qq -y autoclean')
		shutit.send('find / -iname \'mysql*\' | xargs rm -rf')
		shutit.send('rm /root/start_mysql.sh')
		shutit.send('rm /root/stop_mysql.sh')
		return True

	def test(self, shutit):
		mysql_user = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']
		mysql_password = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password']
		root_password = shutit.cfg['shutit.tk.mysql.mysql']['root_password']
		shutit.send('mysql -u' + mysql_user + ' -p' + mysql_password, expect='mysql>', echo=False)
		shutit.send('\q')
		shutit.send('mysql -u' + mysql_user + ' -hlocalhost -p' + mysql_password, expect='mysql>', echo=False)
		shutit.send('\q')
		shutit.send('mysql -u' + mysql_user + ' -hlocalhost -p' + mysql_password, expect='mysql>', echo=False)
		shutit.send('\q')
		shutit.send('mysql -uroot -p' + root_password, expect='mysql>', echo=False)
		shutit.send('\q')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'mysql_user','prince')
		shutit.get_config(self.module_id, 'mysql_user_password','underthecherrymoon')
		shutit.get_config(self.module_id, 'root_password','purple_rain')
		return True

def module():
	return mysql(
		'shutit.tk.mysql.mysql', 0.318,
		description='mysql module. sets up a user/password and the root ' +
			'password, tests all OK.',
		depends=['shutit.tk.setup']
	)

