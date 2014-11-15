FROM progrium/busybox
RUN opkg-install bash gcc bzip2 # possibly can slim further

# Make default shells bash
RUN sed -i 's/^root.*bin.sh/root:x:0:0:root:\/root:\/bin\/bash/' /etc/passwd

RUN echo "ShutIt base distribution 0.1" > /etc/issue

# Needed for ShutIt
ADD base64 /usr/bin/base64
ADD tar /root/tar

# Identify ourselves as a ShutIt distro
# Identify ourselves as a ShutIt distro
CMD ["/bin/bash"]
