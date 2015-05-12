from shutit_module import ShutItModule
import os

class win2048(ShutItModule):

	def build(self, shutit):
		shutit.install('firefox')
		shutit.install('xdotool')
		shutit.install('xautomation')
		shutit.install('vim')
		shutit.install('scrot')
		shutit.install('wget')
		shutit.send("""cat > /root/start_win2048.sh << 'ENDS'
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
		sleep 10
		#Hit key, eg Down for down arrow
		xdotool key KP_${k}
	done
	#Wait for game over to appear
	echo "Waiting for game over"
	sleep 10
	xdotool key KP_Page_Down
	echo "Pushing page down key"
	sleep 10
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
ENDS""", check_exit=False, echo=False)
		shutit.send('pushd /root')
		shutit.send('wget https://raw.githubusercontent.com/ianmiell/shutit/master/library/win2048/files/tryagain.png')
		shutit.send('patextract /root/tryagain.png 0 0 69 20 > /root/tryagain.pat')
		shutit.send('chmod +x /root/start_win2048.sh')
		shutit.send('popd')
		return True

	def remove(self, shutit):
		shutit.send('rm -f /root/start_win2048.sh')
		return True

	def test(self, shutit):
		return shutit.package_installed('firefox') and shutit.package_installed('scrot')

def module():
	return win2048(
		'shutit.tk.win2048.win2048', 0.326,
		description='win at 2048!',
		depends=['shutit.tk.setup', 'shutit.tk.vnc.vnc']
	)

