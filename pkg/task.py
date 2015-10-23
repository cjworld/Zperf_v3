class Task(object):
    
    def __init__(self, protocol_config, server=None, client=None, storage_config=None):
        self._protocol_config = protocol_config
        self._server = server
        self._client = client
        self._storage_config = storage_config

    def setup_task_env(self):
        pass
        
    def cleanup_task_env(self):
        pass
    
    def run_task(self):
        pass
    
class LocalTask(Task):
    
    def setup_task_env(self):
        self._server.setup_storage(self._storage_config, True)
        
    def cleanup_task_env(self):
        self._server.cleanup_storage(self._storage_config, True)
        
    def run_task(self):
        print '[LocalTask] running task.'
    
class NfsTask(Task):
        
    def setup_task_env(self):
        self._server.setup_storage(self._storage_config, True)
        self._setup_nfs_server(self._protocol_config.get("server"))
        self._setup_nfs_client(self._protocol_config.get("client"))
        
    def _setup_nfs_server(self, server_config):
        ''' exports nfs shares on the server '''
        export_configs = server_config.get('exports') or []
        for export_config in export_configs:
            self._server.export_nfs_share(export_config)
        
        ''' enable nfs service on the server '''
        self._server.enable_nfs_server()
        self._server.reload_nfs_shares()
        
    def _setup_nfs_client(self, client_config):
        ''' mount nfs shares on the client '''
        share_configs = client_config.get('shares') or []
        for share_config in share_configs:
            self._client.mount_nfs_share(share_config)
        
    def cleanup_task_env(self):
        self._cleanup_nfs_client(self._protocol_config.get("client"))
        self._cleanup_nfs_server(self._protocol_config.get("server"))
        self._server.cleanup_storage(self._storage_config, True)
        
    def _cleanup_nfs_server(self, server_config):
        ''' disable nfs service on the server '''
        self._server.disable_nfs_server()
        
    def _cleanup_nfs_client(self, client_config):
        ''' unmount nfs shares on the client '''
        share_configs = client_config.get('shares') or []
        for share_config in share_configs:
            self._client.umount_nfs_share(share_config)
        
    def run_task(self):
        print '[NfsTask] running task.'


class IscsiTask(Task):
    
    def setup_task_env(self):
        self._server.setup_storage(self._storage_config, False)
        self._setup_iscsi_server(self._protocol_config.get("server"))
        self._setup_iscsi_client(self._protocol_config.get("client"))
    
    def _setup_iscsi_server(self, server_config):
        
        ''' enable iscsi service on the server '''
        self._server.enable_iscsi_target_service()
        
        ''' add scsi devices '''
        device_configs = server_config.get('devices') or []
        for device_config in device_configs:
            self._server.add_scsi_device(device_config)
                
        ''' create iscsi target and map the scsi devices '''
        target_configs = server_config.get('targets') or []
        for target_config in target_configs:
            self._server.add_iscsi_target(target_config)
            
            portal_configs = target_config.get('portals') or []
            for portal_config in portal_configs:
                self._server.add_iscsi_target_portal(target_config, portal_config)

            acl_configs = target_config.get('acls') or []
            for acl_config in acl_configs:
                self._server.add_iscsi_target_acl(target_config, acl_config)

            lun_configs = target_config.get('luns') or []
            for lun_config in lun_configs:
                self._server.add_iscsi_lun(target_config, lun_config)
                    
            self._server.enable_iscsi_target(target_config)
    
    def _setup_iscsi_client(self, client_config):
        
        ''' enable iscsi client service '''
        self._client.enable_iscsi_service()
    
        ''' login iscsi targets on the client '''
        portal_configs = client_config.get('portals') or []
        for portal_config in portal_configs:
            self._client.add_iscsi_target_portal(portal_config)
            
            target_configs = portal_config.get('targets') or []
            for target_config in target_configs:
                self._client.login_iscsi_target(portal_config, target_config)
      
    def cleanup_task_env(self):
        self._cleanup_iscsi_client(self._protocol_config.get("client"))
        self._cleanup_iscsi_server(self._protocol_config.get("server"))
        self._server.cleanup_storage(self._storage_config, False)
        
    def _cleanup_iscsi_client(self, client_config):
        
        ''' logout iscsi targets on the client '''
        portal_configs = client_config.get('portals') or []
        for portal_config in portal_configs:
            target_configs = portal_config.get('targets') or []
            for target_config in target_configs:
                self._client.logout_iscsi_target(portal_config, target_config)
            #self._client.remove_iscsi_target_portal(portal_config)
                
        ''' disable iscsi client service '''
        self._client.disable_iscsi_service()
        
        
    def _cleanup_iscsi_server(self, server_config):
        
        ''' destroy iscsi target and unmap the scsi devices '''
        target_configs = server_config.get('targets') or []
        for target_config in target_configs:
            
            self._server.disable_iscsi_target(target_config)
            
            lun_configs = target_config.get('luns') or []
            for lun_config in lun_configs:
                self._server.remove_iscsi_lun(target_config, lun_config)
            
            acl_configs = target_config.get('acls') or []
            for acl_config in acl_configs:
                self._server.remove_iscsi_target_acl(target_config, acl_config)

            portal_configs = target_config.get('portals') or []
            for portal_config in portal_configs:
                self._server.remove_iscsi_target_portal(target_config, portal_config)

            self._server.remove_iscsi_target(target_config)
                
        ''' remove scsi devices '''
        device_configs = server_config.get('devices') or []
        for device_config in device_configs:
            self._server.remove_scsi_device(device_config)
                    
        ''' disable iscsi service on the server '''
        self._server.disable_iscsi_target_service()
    
    def run_task(self):
        print '[IscsiTask] running task.'
        
        
class CifsTask(Task):

    def setup_task_env(self):
        self._server.setup_storage(self._storage_config, True)
        self._setup_cifs_server(self._protocol_config.get("server"))
        self._setup_cifs_client(self._protocol_config.get("client"))
        
    def _setup_cifs_server(self, server_config):
        
        ''' reset cifs server configurations '''
        self._server.reset_cifs_settings()
        
        ''' add cifs shares on the server '''
        share_configs = server_config.get('shares') or []
        for share_config in share_configs:
            self._server.add_cifs_share(share_config)
        
        ''' enable cifs service on the server '''
        self._server.enable_cifs_server()
        
    def _setup_cifs_client(self, client_config):
        ''' mount cifs shares on the client '''
        share_configs = client_config.get('shares') or []
        for share_config in share_configs:
            self._client.mount_cifs_share(share_config)
        
    def cleanup_task_env(self):
        self._cleanup_cifs_client(self._protocol_config.get("client"))
        self._cleanup_cifs_server(self._protocol_config.get("server"))
        self._server.cleanup_storage(self._storage_config, True)
        
    def _cleanup_cifs_server(self, server_config):
        ''' disable cifs service on the server '''
        self._server.disable_cifs_server()
        
    def _cleanup_cifs_client(self, client_config):
        ''' remove all cifs shares on the client '''
        share_configs = client_config.get('shares') or []
        for shares_config in share_configs:
            self._client.umount_cifs_share(shares_config)
        
    def run_task(self):
        print '[CifsTask] running task.'
        