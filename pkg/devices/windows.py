from pkg.devices.device import Device
from pkg.protocols.nfs import NFSClient
from pkg.protocols.iscsi import ISCSIClient
from pkg.protocols.cifs import CIFSClient


class WindowsDevice(Device, ISCSIClient, NFSClient, CIFSClient):

    def chmod(self, path, mode):
        if 'mode' == '777':
            self.cmd('cacls  %s /e /g everyone:f' % path)

    def rmdir(self, dir_path):
        self.cmd('rmdir /q %s' % dir_path)

    def mkdir(self, dir_path):
        self.cmd('mkdir %s' % dir_path)

    def mkfile(self, file_path):
        self.cmd('type NUL > %s' % file_path)

    def rm(self, file_path):
        self.cmd('del %s' % file_path)

    def mv(self, src_path, dst_path):
        self.cmd('move /y %s %s' % (src_path, dst_path))

    def reboot(self):
        self.cmd('shutdown -r')

    def mount_cifs_share(self, share_config):
        """
        Mount the cifs share on Windows

        Args:
            share_config: dictionary
                remote_host: '192.168.10.1'
                share_name: 'esshare'
                drive_letter: 'Z'
        """
        remote_host = share_config.get('remote_host')
        share_name = share_config.get('share_name')
        drive_letter = share_config.get('drive_letter')
        if drive_letter and remote_host and share_name:
            command = 'net use %s: \\\\%s\\%s' % (drive_letter.upper(), remote_host, share_name)
            self.cmd(command)

    def umount_cifs_share(self, share_config):
        """
        Unmount the cifs-shared drive

        Args:
            share_config: dictionary
                drive_letter: 'Z'
        """
        drive_letter = share_config.get('drive_letter')
        if drive_letter:
            command = 'net use %s: /delete' % (drive_letter.upper())
            self.cmd(command)

    def mount_nfs_share(self, share_config):
        """
        Mount the nfs share on Windows

        Args:
            share_config: dictionary
                remote_host: 'news'
                remote_dir: '/var/spool/news'
                drive_letter: 'W'
        """
        remote_host = share_config.get('remote_host')
        remote_dir = share_config.get('remote_dir')
        drive_letter = share_config.get('drive_letter')
        if remote_host and remote_dir and drive_letter:
            command = 'mount %s:%s %s:' % (remote_host, remote_dir, drive_letter.upper())
            self.cmd(command)

    def umount_nfs_share(self, share_config):
        """
        Unmount the nfs share on Windows

        Args:
            share_config: dictionary
                drive_letter: 'W'
        """
        drive_letter = share_config.get('drive_letter')
        if drive_letter:
            command = 'umount %s' % (drive_letter.upper())
            self.cmd(command)

    def enable_iscsi_service(self):
        """
        Enable iscsi-related service
        """
        command = 'sc start msiscsi'
        self.cmd(command)

    def disable_iscsi_service(self):
        """
        Disable iscsi-related service
        """
        command = 'sc stop msiscsi'
        self.cmd(command)

    def add_iscsi_target_portal(self, portal_config):
        """
        Add an iSCSI target portal

        Args:
            portal_config: dictionary
                'ip': the ip of the iscsi target portal
        """
        ip = portal_config.get('ip')
        if ip:
            command = 'iscsicli QAddTargetPortal %s' % ip
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
            command = 'iscsicli RemoveTargetPortal %s %d' % (ip, port)
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
        iqn = target_config.get('iqn')
        if iqn:
            command = 'iscsicli QLoginTarget %s' % iqn
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
        iqn = target_config.get('iqn')
        if iqn:
            command = 'iscsicli ReportTargetMappings'
            output = self.cmd(command)
            # TODO parse the output of the targetMappings and find out the right session id

            session = '???'
            command = 'iscsicli LogoutTarget %s' % session
            self.cmd(command)
