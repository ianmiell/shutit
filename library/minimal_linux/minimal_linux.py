
# Created from dockerfile: /space/git/dockerfiles_repos/SvenDowideit/dockerfiles/minimal-linux/Dockerfile
from shutit_module import ShutItModule

class minimal_linux(ShutItModule):

        def is_installed(self, shutit):
                return False

        def build(self, shutit):
        shutit.send('export KERNEL_VERSION=3.14.2')
        shutit.install('wget')
        shutit.send('apt-get update')
        shutit.send('apt-get install -qy fakeroot kernel-package xz-utils bc xorriso syslinux git vim-tiny lib32ncurses5-dev')
        shutit.send('wget -O /linux-3.14.2.tar.xz https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.14.2.tar.xz') 
        shutit.send_host_file('/kernel_config.patch','context/kernel_config.patch')
        shutit.send('xz -d linux-3.14.2.tar.xz')
        shutit.send('tar -xvf linux-3.14.2.tar')
        shutit.send('pushd /linux-3.14.2')
        shutit.send('make defconfig')
        shutit.send('make')
        shutit.send('wget -O /busybox-1.22.1.tar.bz2 http://busybox.net/downloads/busybox-1.22.1.tar.bz2') 
        shutit.send('bunzip2 /busybox-1.22.1.tar.bz2') 
        shutit.send('tar -xvf /busybox-1.22.1.tar') 
        shutit.send_host_file('/busybox-1.22.1.tar.bz2','context/busybox-1.22.1.tar.bz2')
        shutit.send('pushd /busybox-1.22.1')
        shutit.send('make defconfig ; echo "STATIC=y >> .config" >> .config; make ; make install')
        shutit.send('cp -r _install /rootfs ; ls -la /rootfs/bin/busybox')
        shutit.send('pushd /rootfs')
        shutit.send('mkdir dev proc sys tmp')
        shutit.send('mknod dev/console c 5 1')
        shutit.send_host_file('/rootfs/sbin/init','context/init')
        shutit.send_host_file('/isolinux.cfg','context/isolinux.cfg')
        shutit.send('cp /busybox-1.22.1/_install/bin/busybox /rootfs/linuxrc')
        shutit.send('mkdir -p /tmp/iso/boot')
        shutit.send('find | cpio -o -H newc | gzip > /tmp/iso/boot/initrd.gz')
        shutit.send('cp -v /linux-3.14.2/arch/x86_64/boot/bzImage /tmp/iso/boot/vmlinuz64')
        shutit.send('cp /usr/lib/syslinux/isolinux.bin /tmp/iso/boot/')
        shutit.send('cp /isolinux.cfg /tmp/iso/boot/')
        shutit.send('cp /busybox-1.22.1/_install/bin/busybox /tmp/iso/linuxrc')
        shutit.send('echo "SVEN" >> /tmp/iso/version')
        shutit.send('xorriso -as mkisofs -l -J -R -V sven -no-emul-boot -boot-load-size 4 -boot-info-table -b boot/isolinux.bin -c boot/boot.cat -isohybrid-mbr /usr/lib/syslinux/isohdpfx.bin -o /sven.iso /tmp/iso')
        shutit.send('popd')
        shutit.send('popd')
        shutit.send('popd')
                return True

    def finalize(self, shutit):
        return True

    def test(self, shutit):
        return True

    def is_installed(self, shutit):
        return False

    def get_config(self, shutit):
        return True

def module():
        return minimal_linux(
                'shutit.tk.minimal_linux.minimal_linux', 0.1561245235,
                depends=['shutit.tk.setup']
        )
