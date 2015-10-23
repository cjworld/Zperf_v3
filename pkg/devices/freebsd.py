from pkg.devices.device import Device, Server
from pkg.protocols.nfs import NFSServer
from pkg.protocols.iscsi import ISCSIServer
from pkg.protocols.cifs import CIFSServer


class FreeBSDDevice(Device, Server, CIFSServer, ISCSIServer, NFSServer):

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

    def destroy_pool(self, pool_config):
        self.cmd('zpool destroy %s' % pool_config.get('pool_name'))

    def create_pool(self, pool_config):
        slot2path = self._slot2path()

        pool_create_cmd = self._get_create_pool_cmd(pool_config, slot2path)
        self.cmd(pool_create_cmd)

        pool_name = pool_config.get('pool_name')
        self.cmd('zpool add %s qlog ramdisk0' % pool_name)

        global_cache_slots = pool_config.get('globalcache')
        if global_cache_slots:
            global_caches_paths = [slot2path[slot] if slot.startswith('h.') else slot for slot in global_cache_slots]
            self.cmd("zpool add %s cache %s" % (pool_name, ','.join(global_caches_paths)))

    def create_volume(self, pool_config, volume_config, filesystem=True):
        volume_args = volume_config.get('zfs') if filesystem else volume_config.get('zvol')
        volume_name = volume_args.get('name')

        command_tokens = ['zfs', 'create']
        for key, value in volume_args.iteritems():
            if key not in ['name', 'o']:
                command_tokens.append('-%s %s' % (key, value))
        volume_optional_args = volume_args.get('o') or {}
        for key, value in volume_optional_args.iteritems():
            command_tokens.append('-o %s=%s' % (key, value))
        command_tokens.append(volume_name)
        self.cmd(' '.join(command_tokens))

        if filesystem and volume_optional_args:
            if volume_optional_args.get('mountpoint'):
                mountpoint = volume_optional_args.get('mountpoint')
                self.mkdir(mountpoint)
                self.chmod(mountpoint, '777')

    def _slot2path(self):
        disk_list = {}
        output = self.cmd('disk -d status')
        for line in output.splitlines():
            tmp = line.split()
            # jobd disk start with s-528,we need to translate it to h.x format
            if tmp[0].startswith('s'):
                str_tokens = tmp[0].rsplit('.')
                tmp[0] = 'h.%d' % (int(str_tokens[1])+16)

            disk_list[tmp[0]] = tmp[10]
        '''
        disk_list = {
            "h.1": "/dev/qnapmp/WF1CYB1883CX7E3",
            "h.4": "/dev/qnapmp/I9UW969SAI023FY",
            "h.5": "/dev/qnapmp/WHTB5QH3DXSC8JD",
            "h.6": "/dev/qnapmp/O6ZSUG47Q1IUB65",
            "h.7": "/dev/qnapmp/6C66Z2I503OPYV9",
            "h.8": "/dev/qnapmp/1YX4L7L5D5N16W6"
        }
        '''
        return disk_list

    @staticmethod
    def _get_create_pool_cmd(pool_config, slot2path_mapping):

        raid_config = {
            'mirror': 2,  # each mirror use 2 disk
            'raidz': 9,  # each raidz use 8+1 disk
            'raidz2': 6,  # each raidz use 4+2 disk
            'raidz3': 7  # each raidz use 4+3 disk
        }

        pool_name = pool_config.get('pool_name')
        pool_type = pool_config.get('raid_level')
        disk_list_slot = pool_config.get('disks') or []
        disk_list = [slot2path_mapping[slot] for slot in disk_list_slot]

        cmd_tokens = ['zpool', 'create', '-f']

        if pool_config.get('globalcache'):
            cmd_tokens.append('-o globalcache=on')

        cmd_tokens.append(pool_name)

        if pool_type in raid_config.keys():
            gp_size = raid_config[pool_type]
            result = [disk_list[i:i+gp_size] for i in range(0, len(disk_list), gp_size)]
            for val in result:
                cmd_tokens = cmd_tokens + [pool_type] + val
        else:
            cmd_tokens = cmd_tokens + disk_list

        return ' '.join(cmd_tokens)

    def enable_nfs_server(self):
        self.cmd('service nfsd onestart')
        # mountd will automatically start when nfsd starts

    def disable_nfs_server(self):
        self.cmd('service nfsd onestop')
        self.cmd('servie mountd stop')

    def reload_nfs_shares(self):
        self.cmd('service mountd reload')

    def export_nfs_share(self, export_config):
        directory = export_config.get('directory')
        hosts = export_config.get('hosts')
        if directory and hosts:
            self.cmd("echo '%s  -network %s' >> /etc/exports" % (directory, ' '.join(hosts)))

    def add_cifs_share(self, share_config):
        share_name = share_config.get('name')
        path = share_config.get('path')
        if share_name and path:
            self.cmd("echo '' >> /usr/local/etc/smb4.conf")
            self.cmd("echo '[%s]' >> /usr/local/etc/smb4.conf" % share_name)
            self.cmd("echo 'comment = Home Directories' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'force user = nobody' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'only guest = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'browseable = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'writable = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'path = %s' >> /usr/local/etc/smb4.conf" % path)
            self.cmd("echo 'create mask = 0777' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'directory mask = 0777' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'public = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'printable = no' >> /usr/local/etc/smb4.conf")
            self.cmd("echo '' >> /usr/local/etc/smb4.conf")

    def reset_cifs_settings(self):
        text = self.cmd('cat /etc/rc.conf')
        if 'smbd_enable=\"YES\"' not in text:
            self.cmd("echo 'smbd_enable=\"YES\"' >> /etc/rc.conf")
            self.cmd("echo 'winbindd_enable=\"YES\"' >> /etc/rc.conf")
            self.cmd("echo 'nmbd_enable=\"YES\"' >> /etc/rc.conf")
        # self.put('./config/staticfiles/smb4.conf', '/usr/local/etc/smb4.conf')
        # self.put('./config/staticfiles/samba_server', '/usr/local/etc/rc.d/samba_server')
        self.chmod('/usr/local/etc/rc.d/samba_server', '777')

    def enable_cifs_server(self):
        self.cmd('service samba_server onestart')

    def disable_cifs_server(self):
        self.cmd('service samba_server onestop')

    def iscsi_modcheck(self):
        output = self.cmd('kldstat | grep scst')
        if not output:
            return False
        for item in output.splitlines():
            for splice in item.split():
                if splice.find('scst'):
                    return True

    def enable_iscsi_target_service(self):
        mod_loaded = self.iscsi_modcheck()
        if not mod_loaded:
            self.cmd('/etc/rc.d/q-scstd start')
        else:
            self.cmd('/etc/rc.d/q-scstd restart')
        # tricky to enable daemon
        self.cmd(' nohup /nas/util/scst/iscsi-scstd >& /dev/null < /dev/null &')

    def disable_iscsi_target_service(self):
        self.cmd('kldunload iscsi_scst.ko')
        self.cmd('kldunload scst_vdisk.ko')
        self.cmd('kldunload scst.ko')
        self.cmd('pkill iscsi-scstd')

    def add_iscsi_target(self, target_config):
        iqn = target_config.get('iqn')
        if iqn:
            self.cmd('/nas/util/scst/iscsiadm add_target %s' % iqn)

    def remove_iscsi_target(self, target_config):
        iqn = target_config.get('iqn')
        if iqn:
            self.cmd('/nas/util/scst/iscsiadm del_target %s' % iqn)

    def enable_iscsi_target(self, target_config):
        iqn = target_config.get('iqn')
        if iqn:
            self.cmd('/nas/util/scst/iscsiadm enable_target %s 1' % iqn)

    def disable_iscsi_target(self, target_config):
        iqn = target_config.get('iqn')
        if iqn:
            self.cmd('/nas/util/scst/iscsiadm enable_target %s 0' % iqn)

    def add_iscsi_target_portal(self, target_config, portal_config):
        iqn = target_config.get('iqn')
        ip = portal_config.get('ip')
        if iqn and ip:
            self.cmd('/nas/util/scst/iscsiadm add_allow_portal %s %s' % (iqn, ip))

    def remove_iscsi_target_portal(self, target_config, portal_config):
        iqn = target_config.get('iqn')
        ip = portal_config.get('ip')
        if iqn and ip:
            self.cmd('/nas/util/scst/iscsiadm del_allow_portal %s %s' % (iqn, ip))

    def add_iscsi_target_acl(self, target_config, acl_config):
        iqn = target_config.get('iqn')
        domain = acl_config.get('domain')
        if iqn and domain:
            self.cmd('/nas/util/scst/iscsiadm add_acl_network %s %s' % (iqn, domain))

    def remove_iscsi_target_acl(self, target_config, acl_config):
        iqn = target_config.get('iqn')
        domain = acl_config.get('domain')
        if iqn and domain:
            self.cmd('/nas/util/scst/iscsiadm del_acl_network %s %s' % (iqn, domain))

    def add_scsi_device(self, device_config):
        device_name = device_config.get('device_name')
        file_path = device_config.get('file_path')
        if device_name and file_path:
            self.cmd('/nas/util/scst/scsidevadm add_device -n %s -h vdisk_blockio -f %s' % (device_name, file_path))

    def remove_scsi_device(self, device_config):
        device_name = device_config.get('device_name')
        if device_name:
            self.cmd('/nas/util/scst/scsidevadm del_device -n %s -h vdisk_blockio' % device_name)

    def add_iscsi_lun(self, target_config, lun_config):
        iqn = target_config.get('iqn')
        lun = lun_config.get('lun')
        device_name = lun_config.get('device_name')
        if iqn and lun and device_name:
            self.cmd('/nas/util/scst/scstadm add_lun -d iscsi -t %s -l %s -D %s -e 0' % (iqn, lun, device_name))

    def remove_iscsi_lun(self, target_config, lun_config):
        iqn = target_config.get('iqn')
        lun = lun_config.get('lun')
        if iqn and lun:
            self.cmd('/nas/util/scst/scstadm del_lun -d iscsi -t %s -l %s' % (iqn, lun))
