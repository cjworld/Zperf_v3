class IscsiClient:
	
	def enable_iscsi_service(self):
		pass
	
	def disable_iscsi_service(self):
		pass
	
	def add_iscsi_target_portal(self, portal_config):
		pass

	def remove_iscsi_target_portal(self, portal_config):
		pass

	def login_iscsi_target(self, portal_config, target_config):
		pass
	
	def logout_iscsi_target(self, portal_config, target_config):
		pass

class CifsClient:
	
	def mount_cifs_share(self, share_config):
		pass
	
	def umount_cifs_share(self, share_config):
		pass

class NfsClient:
	
	def mount_nfs_share(self, share_config):
		pass
	
	def umount_nfs_share(self, share_config):
		pass

class IscsiServer:

	def enable_iscsi_target_service(self):
		pass	
		
	def disable_iscsi_target_service(self):
		pass
	
	def add_iscsi_target(self, target_config):
		pass
	
	def remove_iscsi_target(self, target_config):
		pass
	
	def enable_iscsi_target(self, target_config):
		pass
	
	def disable_iscsi_target(self, target_config):
		pass
	
	def add_iscsi_target_portal(self, target_config, portal_config):
		pass
	
	def remove_iscsi_target_portal(self, target_config, portal_config):
		pass
	
	def add_iscsi_target_acl(self, target_config, acl_config):
		pass
	
	def remove_iscsi_target_acl(self, target_config, acl_config):
		pass
	
	def add_scsi_device(self, device_config):
		pass
	
	def remove_scsi_device(self, device_config):
		pass
	
	def add_iscsi_lun(self, target_config, lun_config):
		pass
	
	def remove_iscsi_lun(self, target_config, lun_config):
		pass

class CifsServer:
	
	def reset_cifs_settings(self):
		pass
	
	def add_cifs_share(self, share_config):
		pass
	
	def enable_cifs_server(self):
		pass
	
	def disable_cifs_server(self):
		pass
	
class NfsServer:
	
	def reload_nfs_shares(self):
		pass
	
	def export_nfs_share(self, export_config):
		pass
	
	def enable_nfs_server(self):
		pass
	
	def disable_nfs_server(self):
		pass
