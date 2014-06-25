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

class mysql(ShutItModule):

	def is_installed(self,shutit):
		return shutit.file_exists('/root/start_mysql.sh')

	def build(self,shutit):
		root_pass = shutit.cfg['shutit.tk.mysql.mysql']['root_password']
		shutit.install('sudo')
		shutit.send_and_expect("apt-get update")
		shutit.send_and_expect("""debconf-set-selections << 'END'
mysql-server mysql-server/root_password password {0}
END""".format(root_pass),echo=False)
		shutit.send_and_expect("""debconf-set-selections << 'END'
mysql-server mysql-server/root_password_again password {0}
END""".format(root_pass),echo=False)
		shutit.install('mysql-common')
		shutit.install('mysql-server')
		shutit.install('libmysqlclient-dev')
		shutit.send_and_expect('mysqld &')
		shutit.send_and_expect('sleep 2')
		shutit.send_and_expect('mysql_install_db --user=mysql --basedir=/usr --datadir=/var/mysql/database')
		# http://stackoverflow.com/questions/15663001/remote-connections-mysql-ubuntu
		shutit.send_and_expect("perl -p -i -e 's/^bind.*/bind-address = 0.0.0.0/' /etc/mysql/my.cnf")
		mysql_user = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']
		res = shutit.send_and_expect('mysql -p',expect=['assword','mysql>'])
		if res == 0:
			shutit.send_and_expect(root_pass,expect='mysql>',echo=False)
		shutit.send_and_expect("create user '" + mysql_user + "'@'localhost' identified by '" + mysql_user + "';",expect='mysql>')
		shutit.send_and_expect("create user '" + mysql_user + "'@'%' identified by '" + mysql_user + "';",expect='mysql>')
		shutit.send_and_expect("grant all privileges on *.* to '" + mysql_user + "'@'localhost';",expect='mysql>')
		shutit.send_and_expect("grant all privileges on *.* to '" + mysql_user + "'@'%';",expect='mysql>')
		shutit.send_and_expect("set password for " + mysql_user + "@'localhost' = password('" + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + "');",expect='mysql>',echo=False)
		shutit.send_and_expect("set password for " + mysql_user + "@'%' = password('" + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + "');",expect='mysql>',echo=False)
		shutit.send_and_expect(r'\q')
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
		shutit.send_and_expect('chmod +x /root/start_mysql.sh')
		shutit.send_and_expect('chmod +x /root/stop_mysql.sh')
		shutit.send_and_expect('/root/stop_mysql.sh')
		shutit.send_and_expect('/root/start_mysql.sh')
		return True

	def start(self,shutit):
		shutit.send_and_expect('/root/start_mysql.sh',check_exit=False)
		return True

	def stop(self,shutit):
		shutit.send_and_expect('/root/stop_mysql.sh',check_exit=False)
		return True

	def remove(self,shutit):
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
		mysql_user = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user']
		mysql_password = shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password']
		root_password = shutit.cfg['shutit.tk.mysql.mysql']['root_password']
		shutit.send_and_expect('mysql -u' + mysql_user + ' -p' + mysql_password,expect='mysql>',echo=False)
		shutit.send_and_expect('\q')
		shutit.send_and_expect('mysql -u' + mysql_user + ' -hlocalhost -p' + mysql_password,expect='mysql>',echo=False)
		shutit.send_and_expect('\q')
		shutit.send_and_expect('mysql -u' + mysql_user + ' -hlocalhost -p' + mysql_password,expect='mysql>',echo=False)
		shutit.send_and_expect('\q')
		shutit.send_and_expect('mysql -uroot -p' + root_password,expect='mysql>',echo=False)
		shutit.send_and_expect('\q')
		return True

	def get_config(self,shutit):
		shutit.get_config('shutit.tk.mysql.mysql','mysql_user','prince')
		shutit.get_config('shutit.tk.mysql.mysql','mysql_user_password','underthecherrymoon')
		shutit.get_config('shutit.tk.mysql.mysql','root_password','purple_rain')
		return True

def module():
	return mysql(
		'shutit.tk.mysql.mysql', 0.318,
		description='mysql module. sets up a user/password and the root ' +
			'password, tests all OK.',
		depends=['shutit.tk.setup']
	)

