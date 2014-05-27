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

class wordpress(ShutItModule):

	def is_installed(self,shutit):
		return False

	def build(self,shutit):
		shutit.install('apache2')
		shutit.install('wordpress')
		apache_site = """cat > /etc/apache2/sites-available/wordpress << END
        Alias /blog /usr/share/wordpress
        Alias /blog/wp-content /var/lib/wordpress/wp-content
        <Directory /usr/share/wordpress>
            Options followSymLinks
            Allowoverride Limit Options FileInfo
            Directoryindex index.php
            Order allow,deny
            Allow from all
        </Directory>
        <Directory /var/lib/wordpress/wp-content>
            Options followSymLinks
            Order allow,deny
            Allow from all
        </Directory>
END"""
		shutit.send_and_expect(apache_site)
		wordpress_mysql = """cat > /etc/wordpress/config-localhost.php << END
<?php
define('DB_NAME', 'wordpress');
define('DB_USER', 'wordpress');
define('DB_PASSWord', """ + shutit.cfg['shutit.tk.wordpress.wordpress']['password'] + """
define('DB_HOST', 'localhost');
define('WP_CONTEnt_dir', '/var/lib/wordpress/wp-content');
?>
END"""
		shutit.send_and_expect(wordpress_mysql)
		sql = """cat > /tmp/sql << END
CREATE DATABASE wordpress;
GRANT SELECT,INSert,update,DELETE,CREATE,DROP,ALTER
ON wordpress.*
TO wordpress@localhost
IDENTIFIED BY 'yourpasswordhere';
FLUSH PRIVILEGES;
END"""
		shutit.send_and_expect(sql)
		shutit.send_and_expect('cat /tmp/sql | mysql -u' + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user'] + ' -p' + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + ' && rm /tmp/sql',check_exit=False,record_command=False)
		return True

	def start(self,shutit):
		shutit.send_and_expect('sudo apache2ctl restart')
		return True

	def get_config(self,shutit):
		cp = shutit.cfg['config_parser']
		shutit.cfg['shutit.tk.wordpress.wordpress']['password'] = cp.get('shutit.tk.wordpress.wordpress','password')
		return True

def module():
	return wordpress(
		'shutit.tk.wordpress.wordpress', 0.325,
		description='wordpress setup',
		depends=['shutit.tk.setup', 'shutit.tk.mysql.mysql']
	)

