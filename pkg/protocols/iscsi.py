from abc import ABCMeta, abstractmethod
__author__ = 'Jerry Chen'


class ISCSIClient:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def enable_iscsi_service(self):
        pass

    @abstractmethod
    def disable_iscsi_service(self):
        pass

    @abstractmethod
    def add_iscsi_target_portal(self, portal_config):
        pass

    @abstractmethod
    def remove_iscsi_target_portal(self, portal_config):
        pass

    @abstractmethod
    def login_iscsi_target(self, portal_config, target_config):
        pass

    @abstractmethod
    def logout_iscsi_target(self, portal_config, target_config):
        pass


class ISCSIServer:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def enable_iscsi_target_service(self):
        pass

    @abstractmethod
    def disable_iscsi_target_service(self):
        pass

    @abstractmethod
    def add_iscsi_target(self, target_config):
        pass

    @abstractmethod
    def remove_iscsi_target(self, target_config):
        pass

    @abstractmethod
    def enable_iscsi_target(self, target_config):
        pass

    @abstractmethod
    def disable_iscsi_target(self, target_config):
        pass

    @abstractmethod
    def add_iscsi_target_portal(self, target_config, portal_config):
        pass

    @abstractmethod
    def remove_iscsi_target_portal(self, target_config, portal_config):
        pass

    @abstractmethod
    def add_iscsi_target_acl(self, target_config, acl_config):
        pass

    @abstractmethod
    def remove_iscsi_target_acl(self, target_config, acl_config):
        pass

    @abstractmethod
    def add_scsi_device(self, device_config):
        pass

    @abstractmethod
    def remove_scsi_device(self, device_config):
        pass

    @abstractmethod
    def add_iscsi_lun(self, target_config, lun_config):
        pass

    @abstractmethod
    def remove_iscsi_lun(self, target_config, lun_config):
        pass
