## MediaWiki

A self-contained instance of MediaWiki with data volume support.

This image contains a basic installation of [MediaWiki][mw], powered by [nginx][nginx] and
[php-fpm][php-fpm]. When first run, the container will not contain a
`LocalSettings.php` and you can run the MediaWiki installer to configure your
wiki:

[mw]: https://www.mediawiki.org/
[nginx]: http://nginx.org/
[php-fpm]: http://php-fpm.org/

    CONFIG_CONTAINER=$(docker run -d nickstenning/mediawiki)

At the end of this process you can place the resulting `LocalSettings.php` in a
directory on the host (say, `/data/wiki`) and restart the container to obtain a
fully-configured MediaWiki installation.

    docker stop $CONFIG_CONTAINER
    docker run -v /data/wiki:/data -d nickstenning/mediawiki

If you already have a `LocalSettings.php` from a previous MediaWiki
installation, you can simply skip the first step.

By default, MediaWiki uploads will also be written to the `images/` directory of
the mounted data volume. This directory will be created if necessary on startup.

### Technical details

For more information, see [the
repository](https://github.com/nickstenning/dockerfiles/tree/master/mediawiki).
