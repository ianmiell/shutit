alfs

A [ShutIt](https://github.com/ianmiell/shutit) module 

You can build the image with:

`docker build -t alfstmp https://raw.githubusercontent.com/ianmiell/shutit/master/library/alfs/Dockerfile`

Then 

```sh
docker cp $(docker run alfstmp) /lfs.tar.xz /tmp/lfs.tar.xz
git clone https://github.com/ianmiell/shutit-distro.git
cd shutit-distro
cp /tmp/lfs.tar.xz base
cd base
docker build .
```

then use that image as a basis for the modules in here:

[Source-built Docker distro](https://github.com/ianmiell/shutit-distro/blob/master/README.md)
