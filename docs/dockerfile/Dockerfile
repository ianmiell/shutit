# Example Dockerfile for test purposes

FROM ubuntu:14.04

# WORKDIR
WORKDIR /

ENV HOME /root

RUN apt-get install -y iputils-ping
RUN ping -c 1 localhost

WORKDIR etc

# RUN
RUN cat /etc/hosts

# COPY
# If <src> is any other kind of file, it is copied individually DONE along with its metadata TODO. In this case, if <dest> ends with a trailing slash /, it will be considered a directory and the contents of <src> will be written at <dest>/base(<src>). DONE
# If <dest> does not end with a trailing slash, it will be considered a regular file and the contents of <src> will be written at <dest>. DONE
COPY dockerfiledir/README.md /tmp/README.md
RUN cat /tmp/README.md
RUN rm /tmp/README.md

# If <dest> doesn't exist, it is created along with all missing directories in its path. DONE
COPY dockerfiledir/README.md /tmp/copytmp/
RUN cat /tmp/copytmp/dockerfiledir/README.md
RUN rm -rf /tmp/copytmp

# If <src> is a directory, the entire directory is copied DONE, including filesystem metadata. TODO
COPY dockerfiledir /tmp/copytmp2/
RUN cat /tmp/copytmp2/dockerfiledir/README.md
RUN rm -rf /tmp/copytmp2


# ADD
# If <dest> does not end with a trailing slash, it will be considered a regular file and the contents of <src> will be written at <dest>. DONE
# If <dest> doesn't exist, it is created along with all missing directories in its path. DONE
ADD dockerfiledir /dockerfiledir
RUN cat /dockerfiledir/subdir/action.sh
RUN rm -rf /dockerfiledir

# If <src> is a directory, the entire directory is copied, DONE including filesystem metadata. TODO
ADD . /dockerfiledirdotcopy
RUN cat /dockerfiledirdotcopy/dockerfiledir/README.md
RUN rm -rf /dockerfiledirdotcopy


# If <src> is any other kind of file, it is copied individually DONE along with its metadata TODO. In this case, if <dest> ends with a trailing slash /, it will be considered a directory and the contents of <src> will be written at <dest>/base(<src>). DONE
ADD dockerfiledir/README.md /tmp/addtmp/
RUN cat /tmp/addtmp/dockerfiledir/README.md
RUN rm -rf /tmp/addtmp

ADD dockerfiledir /tmp/addtmp2/
RUN cat /tmp/addtmp2/dockerfiledir/subdir/action.sh
RUN rm -rf /tmp/addtmp2

# If <src> is a URL and <dest> does not end with a trailing slash, then a file is downloaded from the URL and copied to <dest>. DONE
ADD https://raw.githubusercontent.com/ianmiell/shutit/master/README.md /tmp/shutit/README.md
RUN cat /tmp/shutit/README.md
# If <src> is a URL and <dest> does end with a trailing slash, then the filename is inferred from the URL and the file is downloaded to <dest>/<filename>. For instance, ADD http://example.com/foobar / would create the file /foobar. The URL must have a nontrivial path so that an appropriate filename can be discovered in this case (http://example.com will not work). DONE
ADD https://raw.githubusercontent.com/ianmiell/shutit/master/README.md /tmp/shutit/readmeunderhere/
RUN cat /tmp/shutit/readmeunderhere/ianmiell/shutit/master/README.md
RUN rm -rf /tmp/shutit

# If <src> is a local tar archive in a recognized compression format (identity, gzip, bzip2 or xz) then it is unpacked as a directory. Resources from remote URLs are not decompressed. When a directory is copied or unpacked, it has the same behavior as tar -x: the result is the union of:
#     whatever existed at the destination path and 
#     the contents of the source tree, with conflicts resolved in favor of "2." on a file-by-file basis. TODO
#ADD dockerfilecompressed/a.tar /tmp
#cat /tmp/a
#RUN rm /tmp/a
#
#ADD dockerfilecompressed/a.tar.gz /tmp
#cat /tmp/a
#RUN rm /tmp/a
#
#ADD dockerfilecompressed/a.tar.bz2 /tmp
#cat /tmp/a
#RUN rm /tmp/a
#
#ADD dockerfilecompressed/a.tar.xz /tmp
#cat /tmp/a
#RUN rm /tmp/a

# EXPOSE
EXPOSE 8088
EXPOSE 8089 8090

# VOLUME
VOLUME /tmp
VOLUME ["/home"]

# CMD
CMD ["/bin/bash"]
