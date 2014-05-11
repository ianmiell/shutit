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

class wordpress(ShutItModule):

	def is_installed(self,shutit):
		config_dict = shutit.cfg
		return False

	def build(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.install(container_child,config_dict,'apache2',config_dict['expect_prompts']['root_prompt'])
		util.install(container_child,config_dict,'wordpress',config_dict['expect_prompts']['root_prompt'])
		apache_site = """cat > /etc/apache2/sites-available/wordpress << END
        Alias /blog /usr/share/wordpress
        Alias /blog/wp-content /var/lib/wordpress/wp-content
        <Directory /usr/share/wordpress>
            Options FollowSymLinks
            AllowOverride Limit Options FileInfo
            DirectoryIndex index.php
            Order allow,deny
            Allow from all
        </Directory>
        <Directory /var/lib/wordpress/wp-content>
            Options FollowSymLinks
            Order allow,deny
            Allow from all
        </Directory>
END"""
		util.send_and_expect(container_child,apache_site,config_dict['expect_prompts']['root_prompt'])
		wordpress_mysql = """cat > /etc/wordpress/config-localhost.php << END
<?php
define('DB_NAME', 'wordpress');
define('DB_USER', 'wordpress');
define('DB_PASSWORD', """ + config_dict['shutit.tk.wordpress.wordpress']['password'] + """
define('DB_HOST', 'localhost');
define('WP_CONTENT_DIR', '/var/lib/wordpress/wp-content');
?>
END"""
		util.send_and_expect(container_child,wordpress_mysql,config_dict['expect_prompts']['root_prompt'])
		sql = """cat > /tmp/sql << END
CREATE DATABASE wordpress;
GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,ALTER
ON wordpress.*
TO wordpress@localhost
IDENTIFIED BY 'yourpasswordhere';
FLUSH PRIVILEGES;
END"""
		util.send_and_expect(container_child,sql,config_dict['expect_prompts']['root_prompt'])
		util.send_and_expect(container_child,'cat /tmp/sql | mysql -u' + config_dict['shutit.tk.mysql.mysql']['mysql_user'] + ' -p' + config_dict['shutit.tk.mysql.mysql']['mysql_user_password'] + ' && rm /tmp/sql',config_dict['expect_prompts']['root_prompt'],check_exit=False,record_command=False)
		return True

	def start(self,shutit):
		config_dict = shutit.cfg
		container_child = util.get_pexpect_child('container_child')
		util.send_and_expect(container_child,'sudo apache2ctl restart',config_dict['expect_prompts']['root_prompt'])
		return True

	def stop(self,shutit):
		config_dict = shutit.cfg
		return True

	def get_config(self,shutit):
		config_dict = shutit.cfg
		cp = config_dict['config_parser']
		config_dict['shutit.tk.wordpress.wordpress']['password'] = cp.get('shutit.tk.wordpress.wordpress','password')
		return True


if not util.module_exists('shutit.tk.wordpress.wordpress'):
	obj = wordpress('shutit.tk.wordpress.wordpress',0.325,'Wordpress example ShutIt module')
	obj.add_dependency('shutit.tk.setup')
	obj.add_dependency('shutit.tk.mysql.mysql')
	util.get_shutit_modules().add(obj)
	ShutItModule.register(wordpress)

