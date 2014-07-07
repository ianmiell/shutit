Docker Plex
===========

This is a Dockerfile to set up `Plex Media Server`_.

Build
-----

Build from Dockerfile. If you have a PlexPass, download the latest version of the .deb installation file from the website to this directory and use the Dockerfile. If not, rename the Dockerfile_no_plex_pass to Dockerfile and build with that instead::

	docker build -rm -t plex . 

Create data-only volume::

    docker run -v /config --name plex_config busybox /bin/true

Run
___

The ports to open up come from the info here_. Systemd service file is also available. ::

    docker run -h <plex_host_name> -d --volumes-from plex_config --volumes-from media_data -p 32400:32400 -p 32443:32443 -p 1900:1900/udp -p 32463:32463 -p 5353:5353/udp -p 32410:32410/udp -p 32412:32412/udp -p 32413:32413/udp -p 32414:32414/udp --name plex_run plex

Manage
------

To manage downloaded media (access the media_data volume)::

    # docker run -i -t --rm --volumes-from media_data ubuntu /bin/bash

.. _Plex Media Server: https://plex.tv
.. _here: https://plexapp.zendesk.com/hc/en-us/articles/201543147-What-network-ports-do-I-need-to-allow-through-my-firewall-
