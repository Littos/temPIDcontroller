# temPIDcontroller
Python PID controller for furnace temperature control

This repo now contains Python files for the actual logic and php files for the web interface as well as dummy files for holdong settings.

******************************************************************
Installation instructions (very crude, mostly for my own memmory)
******************************************************************

Setting up a new temp controller Pi

For Raspberry Pi 3?, Raspbian version:

Make basic install of Pi and add a suitable user.

Add user to “sudoers” if not already added.

Check:
grep -Po '^sudo.+:\K.*$' /etc/group

Add user to sudoers: 
sudo adduser USERNAME sudo

Add user to group gpio:
sudo adduser USERNAME gpio

Verify that python3 is installed.

Verify that git is installed.

Create directory to hold controller files
mkdir /home/homedir/Python

Clone python files:
cd /home/homedir/Python
git clone https://github.com/Littos/temPIDcontroller.git

Clone web interface files: Borde inkluderas i pythonfilerna!
cd /home/homedir/Python
git clone https://github.com/Littos/temPIDweb-interface.git

Set up /home/temperatur/temPIDcontroller/volatile to be a RAM instead of on sd card by adding to /etc/fstab
(othervise the SD card may break quickly). 
mkdir /home/temperatur/temPIDcontroller/volatile
tmpfs /home/temperatur/temPIDcontroller/volatile tmpfs nodev,nosuid,size=10M 0 0
Run sudo mount -a to re-mount according to fstab without rebooting
 
Inatall nginx and php-fpm
sudo apt-get install nginx fcgiwrap nginx-doc ssl-cert
sudo apt-get install php-fpm


Configure nginx:

Edit /etc/nginx/sites-available/default:

# You may add here your
# server {
#	...
# }
# statements for each of your virtual hosts to this file

##
# You should look at the following URL's in order to grasp a solid understanding
# of Nginx configuration files in order to fully unleash the power of Nginx.
# http://wiki.nginx.org/Pitfalls
# http://wiki.nginx.org/QuickStart
# http://wiki.nginx.org/Configuration
#
# Generally, you will want to move this file somewhere, and start with a clean
# file but keep this around for reference. Or just disable in sites-enabled.
#
# Please see /usr/share/doc/nginx-doc/examples/ for more detailed examples.
##

server {
	#listen   80; ## listen for ipv4; this line is default and implied

	root /home/temperatur/temPIDcontroller;
	index index.php index.html index.htm;

	# Make site accessible from http://localhost/
	server_name localhost;

	location / {
		# First attempt to serve request as file, then
		# as directory, then fall back to displaying a 404.
		try_files $uri $uri/ /index.html;
	}
	
#	location /volatile {
#		root /home/temperatur/temPIDcontroller/volatile;
#	}

	location /doc/ {
		alias /usr/share/doc/;
		autoindex on;
		allow 127.0.0.1;
		allow ::1;
		deny all;
	}

	# pass the PHP scripts to FastCGI server listening on 127.0.0.1:9000

	location ~ \.php$ {
		fastcgi_split_path_info ^(.+\.php)(/.+)$;

		# With php7.3-fpm:
		fastcgi_pass unix:/run/php/php7.3-fpm.sock;
		fastcgi_index index.php;
		include fastcgi.conf;
	}
}


Re start nginx
sudo /etc/init.d/nginx start
Or
systemctl restart nginx

Start php7.3-fpm
sudo service php7.3-fpm start

Change permissions on files needed to be accessed by nginx:

Make sure /java/ libary is copied to /tempPIDconrtoller alondside with all the relevan php files. 
Download java library for d3.js is downloaded from https://d3js.org/ and placed in /home/HOMEDIR/temPIDcontroller
 
sudo chown -R :www-data java/
cd /home/HOMEDIR/index.php
sudo chown :www-data temPIDcontroller/
cd /home/HOMEDIR/temPIDcontroller
sudo chown :www-data volatile/ *.php seq* data*
Chmod 644 on a number of files that www-data needs to write to
Make cron script to run ./tempPIDcontroller.py at startup
Run
crontab -e
add:
@reboot /home/temperatur/temPIDcontroller/temp_controler.py &

Or use systemd to do the same thing. Remember the & to supress logging.




