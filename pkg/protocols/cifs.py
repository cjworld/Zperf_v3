from abc import ABCMeta, abstractmethod
__author__ = 'Jerry Chen'


class CIFSClient:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def mount_cifs_share(self, share_config):
        pass
    
    @abstractmethod
    def umount_cifs_share(self, share_config):
        pass


class CIFSServer:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def reset_cifs_settings(self):
        pass
    
    @abstractmethod
    def add_cifs_share(self, share_config):
        pass
    
    @abstractmethod
    def enable_cifs_server(self):
        pass
    
    @abstractmethod
    def disable_cifs_server(self):
        pass
