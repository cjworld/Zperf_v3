from pkg.devices.device import Device
from pkg.protocols.nfs import NFSClient
from pkg.protocols.iscsi import ISCSIClient
from pkg.protocols.cifs import CIFSClient


class CentOSDevice(Device, ISCSIClient, NFSClient, CIFSClient):

    def chmod(self, path, mode):
        self.cmd("chmod %s %s" % (mode, path))

    def rmdir(self, dir_path):
        self.cmd("rmdir %s" % dir_path)

    def mkdir(self, dir_path):
        self.cmd("mkdir %s" % dir_path)

    def mkfile(self, file_path):
        self.cmd("echo '' > %s" % file_path)

    def rm(self, file_path):
        self.cmd("rm %s" % file_path)

    def mv(self, src_path, dst_path):
        self.cmd("mv %s %s" % (src_path, dst_path))

    def reboot(self):
        self.cmd("reboot")

    def mount_cifs_share(self, share_config):
        """
            Mount the cifs share on the linux

            Args:
                remote_host: '192.168.10.1'
                share_name: ' esshare'
                mount_point: '/mnt/esshare'
        """
        mount_point = share_config.get('mount_point')
        share_name = share_config.get('share_name')
        remote_host = share_config.get('remote_host')
        if remote_host and share_name and mount_point:
            command = 'mount -t cifs -o guest //%s/%s %s' % (remote_host, share_name, mount_point)
            self.cmd(command)

    def umount_cifs_share(self, **kwargs):
        """
            Unmount the cifs-shared drive on the Linux

            Args:
                mount_point: '/mnt/esshare'
        """
        mount_point = kwargs.get('mount_point')
        if mount_point:
            command = 'umount %s' % mount_point
            self.cmd(command)

    def mount_nfs_share(self, share_config):
        """
            Mount the nfs share on the linux

            Args:
                share_config: dictionary
                    remote_host: 'news'
                    remote_dir: '/var/spool/news'
                    mount_point: '/var/spool/news'
        """
        remote_host = share_config.get('remote_host')
        remote_dir = share_config.get('remote_dir')
        mount_point = share_config.get('mount_point')
        if remote_host and remote_dir:
            if mount_point:
                command = 'mount -t nfs %s:%s %s' % (remote_host, remote_dir, mount_point)
                self.cmd(command)

    def umount_nfs_share(self, share_config):
        """
            Unmount the nfs share on the Linux

            Args:
                share_config: dictionary
                    mount_point: '/mnt/esshare'
        """
        mount_point = share_config.get('mount_point')
        if mount_point:
            command = 'umount %s' % mount_point
            self.cmd(command)

    def enable_iscsi_service(self):
        """
            Enable iscsi-related service
        """
        self.put('multipath.conf', '/etc/multipath.conf')

        command = 'service multipathd start'
        self.cmd(command)

        command = 'multipath -v2'
        self.cmd(command)

    def disable_iscsi_service(self):
        """
            Disable iscsi-related service
        """
        command = 'service multipathd stop'
        self.cmd(command)

    def add_iscsi_target_portal(self, portal_config):
        """
            Add an iSCSI target portal

            Args:
                portal_config: dictionary
                    'ip': the ip of the iscsi target portal
                    'port' the port of the iscsi target portal
        """
        ip = portal_config.get('ip')
        port = portal_config.get('port')
        if ip and port:
            command = 'iscsiadm -m discovery -t sendtargets -p %s:%s' % (ip, port)
            self.cmd(command)

    def remove_iscsi_target_portal(self, portal_config):
        """
            Remove an iSCSI target portal

            Args:
                portal_config: dictionary
                    'ip': the ip of the iscsi target portal
                    'port' the port of the iscsi target portal
        """
        ip = portal_config.get('ip')
        port = portal_config.get('port')
        if ip and port:
            command = 'iscsicli RemoveTargetPortal %s %s' % (ip, port)
            self.cmd(command)

    def login_iscsi_target(self, portal_config, target_config):
        """
            Login an iSCSI target

            Args:
                portal_config: dictionary
                    'ip': the ip of the iscsi target portal
                    'port' the port of the iscsi target portal
                target_config: dictionary
                    'iqn': the iqn of the iscsi target
        """
        ip = portal_config.get('ip')
        port = portal_config.get('port')
        iqn = target_config.get('iqn')
        if ip and port and iqn:
            command = 'iscsiadm -m node -l -T %s -p %s:%d' % (iqn, ip, port)
            self.cmd(command)

    def logout_iscsi_target(self, portal_config, target_config):
        """
            Logout an iSCSI target

            Args:
                portal_config: dictionary
                    'ip': the ip of the iscsi target portal
                    'port' the port of the iscsi target portal
                target_config: dictionary
                    'iqn': the iqn of the iscsi target
        """
        ip = portal_config.get('ip')
        port = portal_config.get('port')
        iqn = target_config.get('iqn')
        if ip and port and iqn:
            command = 'iscsiadm -m node -u -T %s -p %s:%d' % (iqn, ip, port)
            self.cmd(command)
