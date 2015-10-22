import os
import protocols
import fabric.api

    
class Device(object):
    def __init__(self, host=None, port=None, usr=None, pwd=None):
        self._host = host
        self._port = port
        self._usr = usr 
        self._pwd = pwd
    
    def chmod(self, path, mode):
        if os.path.exists(path):
            #os.chmod(path, mode)
            self.cmd("chmod %s %s" % (mode, path))
    
    def rmdir(self, dir_path):
        if os.path.isdir(dir_path):
            os.rmdir(dir_path)
    
    def makedir(self, dir_path, **kwargs):
        if not os.path.isdir(dir_path):
            #os.mkdir(dir_path)
            self.cmd("mkdir %s" % dir_path)
    
    def put(self, src_file_path, dst_file_path):
        pass
    
    def reboot(self, wait=720):
        pass
    
    def cmd(self, command, timeout=30):
        """
            Command the given command on the device

            Args:
                command: command you're going to command

            Kargs:
                timeout: seconds to wait
        """
        host = '%s@%s' % (self._usr, self._host)
        with fabric.api.settings(host_string=host, password=self._pwd):
            return fabric.api.run(command, shell=False, timeout=30, quiet=True)
    
    def setup_storage(self, storage_config, filesystem):
        pass
        
    def cleanup_storage(self, storage_config, filesystem):
        pass
    
    
class LinuxDevice(Device):
    
    def setup_nic(self, nic_name, nic_config):
        nic_ip = nic_config.get('nic_ip')
        nic_netmask = nic_config.get('nic_netmask')
        if nic_ip and nic_netmask:
            self.cmd('ifconfig %s %s netmask %s'% (nic_name, nic_ip, nic_netmask))
            output = self.cmd('ethtool -c %s' % (nic_name))
            for item in output.splitlines():
                if len(item)==0:
                    continue
                elif item.split()[0]=='rx-usecs:' and item.split()[1]!='10':
                    self.cmd('ethtool -C %s rx-usecs 10' % nic_name)
    
    
class WindowsDevice(Device):
    
    def __init__(self, server_config):
        ip = server_config.get('ip')
        port = server_config.get('port')
        usr = server_config.get('username')
        pwd = server_config.get('password')
        super(WindowsDevice, self).__init__(host=ip, port=port, usr=usr, pwd=pwd)
        
        self._network = server_config.get('network')
        nic_configs = self._network.get('nics') or []
        '''
        # No way to reset windows lan
        for nic_config in nic_configs:
            self._setup_nic(nic_config)
        '''
    
    def cmd(self, command):
        cmd_windows = 'cmd.exe /c %s' % command
        return super(WindowsDevice, self).cmd(cmd_windows)
    
    
class FreeBSDDevice(Device):
    
    def __init__(self, server_config):
        ip = server_config.get('ip')
        port = server_config.get('port')
        usr = server_config.get('username')
        pwd = server_config.get('password')
        super(FreeBSDDevice, self).__init__(host=ip, port=port, usr=usr, pwd=pwd)
        
        self._network = server_config.get('network')
        nic_configs = self._network.get('nics') or []
        for nic_config in nic_configs:
            self._setup_nic(nic_config)
    
    def _setup_nic(self, nic_config):
        nic_name = nic_config.get('name')
        nic_ip = nic_config.get('ip')
        nic_netmask = nic_config.get('netmask')
        if nic_name != None and nic_ip != None and nic_netmask != None:
            self.cmd('ifconfig %s %s netmask %s' % (nic_name, nic_ip, nic_netmask))
            nic_driver = nic_config.get('driver')
            nic_driver_index = nic_config.get('driver_index')
            if nic_driver != None and nic_driver_index != None:
                self.cmd('sysctl dev.%s.%d.enable_aim=0' % (nic_driver, nic_driver_index) )
                for j in range(0, 8):
                    self.cmd('sysctl dev.%s.%d.queue%d.interrupt_rate=100000' % (nic_driver, nic_driver_index, j))
    
    def setup_storage(self, storage_config, filesystem):
        pool_configs = storage_config.get('pools') or []
        for pool_config in pool_configs:
            self._create_pool(pool_config)
            
            volume_configs = pool_config.get('volumes') or []
            for volume_config in volume_configs:
                self._create_volume(pool_config, volume_config, filesystem)
    
    def _create_pool(self, pool_config):
        slot2path_mapping = self._slot2path()
        
        pool_create_cmd = self._get_create_pool_cmd(pool_config, slot2path_mapping)
        self.cmd(pool_create_cmd)
        
        pool_name = pool_config.get('pool_name')
        self.cmd('zpool add %s qlog ramdisk0' % pool_name)
        
        global_cache_slots = pool_config.get('globalcache')
        if global_cache_slots:
            global_caches_paths = [ slot2path_mapping[slot] if slot.startswith('h.') else slot for slot in global_cache_slots]
            self.cmd("zpool add %s cache %s" % (pool_name, ','.join(global_caches_paths)))
                
    def _create_volume(self, pool_config, volume_config, filesystem):
        
        volume_args = volume_config.get('zfs') if filesystem else volume_config.get('zvol')
        volume_name = volume_args.get('name')
        
        command_toks = ['zfs', 'create']
        for key, value in volume_args.iteritems():
            if key not in ['name', 'o']:
                command_toks.append('-%s %s' % (key, value))
        volume_optional_args = volume_args.get('o') or {}
        for key, value in volume_optional_args.iteritems():
            command_toks.append('-o %s=%s' % (key, value))
        command_toks.append(volume_name)
        self.cmd(' '.join(command_toks))
        
        if filesystem and volume_optional_args:
            if volume_optional_args.get('mountpoint'):
                mountpoint = volume_optional_args.get('mountpoint')
                self.makedir(mountpoint)
                self.chmod(mountpoint, '777')
        
    def cleanup_storage(self, storage_config, filesystem):
        pool_configs = storage_config.get('pools') or []
        for pool_config in pool_configs:
            self.cmd('zpool destroy %s' % pool_config.get('pool_name'))

    def _get_create_pool_cmd(self, pool_config, slot2path_mapping):
        
        raid_config = {
            'mirror': 2, #each mirror use 2 disk
            'raidz': 9, #each raidz use 8+1 disk
            'raidz2': 6, #each raidz use 4+2 disk
            'raidz3': 7 #each raidz use 4+3 disk
        }
        
        poolname = pool_config.get('pool_name')
        pooltype = pool_config.get('raid_level')
        disklist_slot = pool_config.get('disks') or []
        disklist = [ slot2path_mapping[slot] for slot in disklist_slot ]

        cmd_toks = ['zpool', 'create', '-f']
        
        if pool_config.get('globalcache'):
            cmd_toks.append('-o globalcache=on')
                
        cmd_toks.append(poolname)
        
        if pooltype in raid_config.keys():
            gp_size = raid_config[pooltype]
            result = [disklist[i:i+gp_size] for i in range(0, len(disklist), gp_size)]
            for val in result:
                cmd_toks = cmd_toks + [pooltype] + val
        else:
            cmd_toks = cmd_toks + disklist
                
        return ' '.join(cmd_toks)

    def _slot2path(self):
        es_disklist = {}
        output = self.cmd('disk -d status')
        '''
        for line in output.splitlines():
            tmp = line.split()
            # jobd disk start with s-528,we need to translate it to h.x format
            if tmp[0].startswith('s'):
                str = tmp[0].rsplit('.')
                tmp[0] ='h.%d'%(int(str[1])+16)
                
            es_disklist[tmp[0]] = tmp[10]
        '''    
        es_disklist = {
            "h.1": "/dev/qnapmp/WF1CYB1883CX7E3",
            "h.4": "/dev/qnapmp/I9UW969SAI023FY",
            "h.5": "/dev/qnapmp/WHTB5QH3DXSC8JD",
            "h.6": "/dev/qnapmp/O6ZSUG47Q1IUB65",
            "h.7": "/dev/qnapmp/6C66Z2I503OPYV9",
            "h.8": "/dev/qnapmp/1YX4L7L5D5N16W6"
        }
            
        return es_disklist
    '''
    def _get_fw_ver(self):
        fw_ver = 0
        output = self.cmd('ver -v');
        result = output.splitlines()[0].split()[0]    
        idx = result.rindex('-')
        #get ES firmware version
        fw_ver = result[idx+1:]
        return fw_ver
        
    def _get_zfs_ver(self):
        zfs_ver = 0
        output = self.cmd('ver -v');
        #get zfs-stable version
        for item in output.splitlines():
            for splice in item.split():
                if splice.startswith('zfs-stable'):
                    result = splice.split()[0]
                    idx = result.rindex('-')
                    zfs_ver = int(result[idx+1:])
        return zfs_ver
        
    def switch_fwver(self, index):
        if index >= len(fwver_list):
            return
        
        with settings(
            hide('stdout'),
            host_string=self._dbconf['server_host'],password=self._dbconf['server_password'],
            warn_only=True
        ):
            output = run('ifconfig -L em0')
            for line in output.splitlines():
                tmp = line.split()
                if tmp[0].startswith('ether'):
                    self._mac = tmp[1]
            
            url='http://10.77.157.1:8000/sanboot/load?MAC=%s&IP=%s&FW=%s'%(self._mac.replace(':','%3A'),self._dbconf['server_host'],fwver_list[index])
            #print url
            http_sanboot = urllib3.PoolManager()
            http_sanboot.request('GET', url)
            reboot(wait=720)
            print (green('Rebooting,switch to next firmware version %s.......[OK]'%fwver_list[index],bold=True))
    '''
        
    
class FreeBSDServer(FreeBSDDevice, protocols.NfsServer, protocols.IscsiServer):
    
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
            self.cmd("echo '[%s]' >> /usr/local/etc/smb4.conf" % (share_name))
            self.cmd("echo 'comment = Home Directories' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'force user = nobody' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'only guest = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'browseable = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'writable = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'path = %s' >> /usr/local/etc/smb4.conf" % (path))
            self.cmd("echo 'create mask = 0777' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'directory mask = 0777' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'public = yes' >> /usr/local/etc/smb4.conf")
            self.cmd("echo 'printable = no' >> /usr/local/etc/smb4.conf")
            self.cmd("echo '' >> /usr/local/etc/smb4.conf")
    
    def reset_cifs_settings(self):
        text = self.cmd('cat /etc/rc.conf')
        text = "123"
        if 'smbd_enable=\"YES\"' not in text:
            self.cmd("echo 'smbd_enable=\"YES\"' >> /etc/rc.conf")
            self.cmd("echo 'winbindd_enable=\"YES\"' >> /etc/rc.conf")
            self.cmd("echo 'nmbd_enable=\"YES\"' >> /etc/rc.conf")
        self.put('./config/staticfiles/smb4.conf', '/usr/local/etc/smb4.conf')
        self.put('./config/staticfiles/samba_server', '/usr/local/etc/rc.d/samba_server')
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
        #tricky to enable daemon 
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
            self.cmd('/nas/util/scst/iscsiadm add_acl_network %s %s'%(iqn, domain))
        
    def remove_iscsi_target_acl(self, target_config, acl_config):
        iqn = target_config.get('iqn')
        domain = acl_config.get('domain')
        if iqn and domain:
            self.cmd('/nas/util/scst/iscsiadm del_acl_network %s %s'%(iqn, domain))
    
    def add_scsi_device(self, device_config):
        device_name = device_config.get('device_name')
        file_path = device_config.get('file_path')
        if device_name and file_path:
            self.cmd('/nas/util/scst/scsidevadm add_device -n %s -h vdisk_blockio -f %s' % (device_name, file_path))
    
    def remove_scsi_device(self, device_config):
        device_name = device_config.get('device_name')
        if device_name:
            self.cmd('/nas/util/scst/scsidevadm del_device -n %s -h vdisk_blockio' % (device_name))
    
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
    
'''
class LinuxClient(Device, NfsClient, CifsClient, IscsiClient):

	def mount_cifs_share(self, **kwargs):
		"""
			Mount the cifs share on the linux

			Args:
				share_path: ' //192.168.10.1/esshare'
				mount_point: '/mnt/esshare'
		"""
		mount_point = kwargs.get('mount_point')
		share_path = kwargs.get('share_path')
		username = kwargs.get('username')
		password = kwargs.get('password')
		if mount_point and share_path:
			if username and password:
				command = 'mount -t cifs %s %s -o username=%s,password=%s' % (share_path, mount_point, username, password)
				self.cmd(command)

	def umount_cifs_share(self, **kwargs):
		"""
			Unmount the cifs-shared drive on the Linux

			Args:
				mount_point: '/mnt/esshare'
		"""
		mount_point = kwargs.get('mount_point')
		if mount_point:
			command = 'umount %s' % (mount_point)
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
			command = 'umount %s' % (mount_point)
			self.cmd(command)

	def enable_iscsi_service(self):
		"""
			Enable iscsi-related service
		"""
		put('multipath.conf','/etc/multipath.conf')

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
'''

class WindowsClient(WindowsDevice, protocols.NfsClient, protocols.IscsiClient, protocols.CifsClient):

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
            command = 'iscsicli QAddTargetPortal %s' % (ip)
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
            command = 'iscsicli QLoginTarget %s' % (iqn)
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
            command = 'iscsicli LogoutTarget %s' % (session)
            self.cmd(command)


if __name__ == "__main__":
    import json
    import task

    with open('./configs/servers/FreeBSD.json', 'r') as fp:
        srvcfg = json.load(fp)
        a = FreeBSDServer(srvcfg)

        with open('./configs/storages/Template.json', 'r') as fp_str:
            stgcfg = json.load(fp_str)
            a.setup_storage(stgcfg, True)
    '''
            with open('./configs/protocols/CIFS.json', 'r') as fp_prt:
                protocol_config = json.load(fp_prt)
                
                with open('./configs/clients/Windows.json', 'r') as fp_cli:
                    client_config = json.load(fp_cli)
                    b = WindowsClient(client_config)
                    
                    task = task.CifsTask(protocol_config, server=a, client=b, storage_config=storage_config)
                    task.setup_task_env()
                    task.cleanup_task_env()
                
            #a.cleanup_storage(storage_config, True)
    '''