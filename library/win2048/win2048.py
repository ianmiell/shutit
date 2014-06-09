#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is furnished
#to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from shutit_module import ShutItModule
import os

class win2048(ShutItModule):

	def is_installed(self,shutit):
		return self.test(shutit)

	def build(self,shutit):
		shutit.install('firefox')
		shutit.install('xdotool')
		shutit.install('xautomation')
		shutit.install('vim')
		shutit.install('scrot')
		shutit.install('wget')
		shutit.send_and_expect("""cat > /root/start_win2048.sh << 'ENDS'
#!/bin/bash
# start vnc
rm -rf /tmp/.X*
vncserver << END
""" + shutit.cfg['shutit.tk.vnc.vnc']['password'] + """
""" + shutit.cfg['shutit.tk.vnc.vnc']['password'] + """
END
echo "Did you expose ports 5901 and 6080?"
echo "If so, then vnclient localhost:1 should work."
export DISPLAY=:1
xdotool exec firefox
WID=$(xdotool search --sync --onlyvisible --class firefox)
echo $WID
# Wait for things to load
xdotool sleep 10
# Destroy the gnome terminal
killall gnome-terminal
# Focus on the ff window
xdotool windowfocus $WID
# Go to address bar
xdotool key F6
# Type address in
xdotool type http://gabrielecirulli.github.io/2048/
# Go.
xdotool key KP_Enter
#Wait for page to load
sleep 5

## Example for automating single attempt repeatedly
if [[ x$keys != 'x' ]]
then
	for k in $keys
	do	
		echo "pressing $k"
		sleep 1
		#Hit key, eg Down for down arrow
		xdotool key KP_${k}
	done
	#Wait for game over to appear
	echo "Waiting for game over"
	sleep 5
	xdotool key KP_Page_Down
	echo "Pushing page down key"
	sleep 2
	# Take a screenshot, which either has "try again on it, or doesn't"
	scrot -q 100 -u /root/a.png
	# extract the pat file
	patextract /root/tryagain.png 0 0 69 20 > /root/tryagain.pat
	# is it there?
	# 0 = match(es)
	# 1 = no match
	# else error
	echo "Searching for 'try again' image"
	visgrep -x 0 -y 0 -t 100000 /root/a.png /root/tryagain.pat /root/tryagain.pat
	res=$?
	if [[ $res = 1 ]]
	then
		echo "OK - no 'try again' found"
	else
		echo "FAIL - 'try again' seen"
		exit 1
	fi
fi
/bin/bash
ENDS""",check_exit=False)
		shutit.send_and_expect('pushd /root')
		shutit.send_and_expect('wget https://raw.githubusercontent.com/ianmiell/shutit/master/library/win2048/files/tryagain.png')
		shutit.send_and_expect('patextract /root/tryagain.png 0 0 69 20 > /root/tryagain.pat')
		shutit.send_and_expect('chmod +x /root/start_win2048.sh')
		shutit.send_and_expect('popd')
		return True

	def remove(self,shutit):
		shutit.send_and_expect('rm -f /root/start_win2048.sh')
		return True

	def test(self,shutit):
		return shutit.package_installed('firefox') and shutit.package_installed('scrot')

def module():
	return win2048(
		'shutit.tk.win2048.win2048', 0.326,
		description='win at 2048',
		depends=['shutit.tk.setup', 'shutit.tk.vnc.vnc', 'shutit.tk.squid_deb_proxy.squid_deb_proxy']
	)

