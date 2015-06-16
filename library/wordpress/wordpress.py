from shutit_module import ShutItModule

#https://www.digitalocean.com/community/tutorials/how-to-install-wordpress-on-ubuntu-14-04

class wordpress(ShutItModule):

	def build(self, shutit):
		shutit.install('apache2 wget php5-gd libssh2-php')
		shutit.send('wget -qO- http://wordpress.org/latest.tar.gz | tar -zxvf -')
		shutit.send('cd wordpress')
		shutit.send('cp wp-config-sample.php wp-config.php')
		shutit.replace_text('''define('DB_NAME', 'wordpress');''','wp-config.php',r'.*DB_NAME.*;')
		shutit.pause_point('wp-config.php')
#define('DB_USER', 'wordpressuser');
#define('DB_PASSWORD', 'password');

		apache_site = """cat > /etc/apache2/sites-available/wordpress << END
		Alias /blog /usr/share/wordpress
		Alias /blog/wp-content /var/lib/wordpress/wp-content
		<Directory /usr/share/wordpress>
			Options followSymLinks
			Allowoverride Limit Options FileInfo
			Directoryindex index.php
			Order allow, deny
			Allow from all
		</Directory>
		<Directory /var/lib/wordpress/wp-content>
			Options followSymLinks
			Order allow, deny
			Allow from all
		</Directory>
END"""
		shutit.send(apache_site)
		wordpress_mysql = """cat > /etc/wordpress/config-localhost.php << END
<?php
define('DB_NAME', 'wordpress');
define('DB_USER', 'wordpress');
define('DB_PASSWord', """ + shutit.cfg['shutit.tk.wordpress.wordpress']['password'] + """)
define('DB_HOST', 'localhost');
define('WP_CONTEnt_dir', '/var/lib/wordpress/wp-content');
?>
END"""
		shutit.send(wordpress_mysql)
		sql = """cat > /tmp/sql << END
CREATE DATABASE wordpress;
GRANT SELECT, INSert, update, DELETE, CREATE, DROP, ALTER
ON wordpress.*
TO wordpress@localhost
IDENTIFIED BY 'yourpasswordhere';
FLUSH PRIVILEGES;
END"""
		shutit.send(sql)
		shutit.send('cat /tmp/sql | mysql -u' + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user'] + ' -p' + shutit.cfg['shutit.tk.mysql.mysql']['mysql_user_password'] + ' && rm /tmp/sql', check_exit=False, record_command=False)
		return True

	def start(self, shutit):
		shutit.send('apache2ctl restart')
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'password','lovesexy')
		return True

def module():
	return wordpress(
		'shutit.tk.wordpress.wordpress', 0.325,
		description='wordpress setup',
		depends=['shutit.tk.setup', 'shutit.tk.mysql.mysql']
	)

