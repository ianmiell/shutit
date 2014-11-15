FROM progrium/busybox
RUN opkg-install bash gcc bzip2 # possibly can slim further
RUN echo "ShutIt base distribution 0.1" > /etc/issue
CMD ["/bin/bash"]
