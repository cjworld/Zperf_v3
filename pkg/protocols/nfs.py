from abc import ABCMeta, abstractmethod
__author__ = 'Jerry Chen'


class NFSClient:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def mount_nfs_share(self, share_config):
        pass

    @abstractmethod
    def umount_nfs_share(self, share_config):
        pass


class NFSServer:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def reload_nfs_shares(self):
        pass

    @abstractmethod
    def export_nfs_share(self, export_config):
        pass

    @abstractmethod
    def enable_nfs_server(self):
        pass

    @abstractmethod
    def disable_nfs_server(self):
        pass
