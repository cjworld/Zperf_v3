from abc import ABCMeta, abstractmethod
import os
__author__ = 'Jerry Chen'


class Device:
    __metaclass__ = ABCMeta

    def __init__(self, host=None, port=None, usr=None, pwd=None):
        self._host = host
        self._port = port
        self._usr = usr
        self._pwd = pwd
        self._services = {}

    def register_service(self, service_name, service_instance):
        self._service[service_name] = service_instance

    def setup_service(self, service_name, service_config):
        if self._service.get(service_name):
            self._service[service_name].setup(self, service_config)
        else:
            raise Exception

    def cleanup_service(self, service_name, service_config):
        if self._service.get(service_name):
            self._service[service_name].cleanup(self, service_config)
        else:
            raise Exception

    @abstractmethod
    def chmod(self, path, mode):
        pass

    @abstractmethod
    def rmdir(self, dir_path):
        pass

    @abstractmethod
    def mkdir(self, dir_path):
        pass

    @abstractmethod
    def mkfile(self, file_path):
        pass

    @abstractmethod
    def rm(self, file_path):
        pass

    @abstractmethod
    def mv(self, src_path, dst_path):
        pass

    @abstractmethod
    def reboot(self):
        pass

    def cmd(self, command):
        #cmd_windows = 'cmd.exe /c %s' % command
        #return super(WindowsDevice, self).cmd(cmd_windows)
        print '[cmd] %s' % command
        os.system(command)


class Server:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def create_pool(self, pool_config):
        pass

    @abstractmethod
    def create_volume(self, pool_config, volume_config, filesystem=True):
        pass

    @abstractmethod
    def destroy_pool(self, pool_config):
        pass

