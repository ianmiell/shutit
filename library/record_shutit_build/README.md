record_shutit_build: 
VNC, ttygif and shutit in one container.

To use:

```sh
docker run -d -p 5901:5901 -p 6080:6080 imagename /bin/bash -c '/root/start_vnc.sh && sleep infinity'
```

Then:

```sh
vncviewer localhost:1
```

Default password in shutit is: vncpass (configurable in vnc module)

Then set up your configuration file, eg:

```sh
cat > ~/.shutit/config << END
	TODO
END
```

Then run your shutit build. The delivery within this image takes place over bash by default.

Then commit your container, tag and push as normal.


Want to deliver into a docker container?
Docker-in-docker is included, but the setup is trickier.
TODO
