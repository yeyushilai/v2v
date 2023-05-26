# -*- coding: utf-8 -*-

"""功能：源平台类"""

from log.logger import logger

from base import Base
from context import WorkerContext
from resource_control.vmware_vsphere.interface import VsphereInterface

CTX = WorkerContext()


def connect(func):
    def inner(vmware_platform, *args, **kwargs):
        account = {
            "host": vmware_platform.ip,
            "user": vmware_platform.user,
            "encrypt_password": vmware_platform.password,
            "port": vmware_platform.port
        }
        vsphere_interface = VsphereInterface(account)
        vmware_platform.vsphere_interface = vsphere_interface
        return func(vmware_platform, *args, **kwargs)

    return inner


class Platform(Base):
    def __init__(self, platform_id):
        super(Platform, self).__init__()
        self._platform_id = platform_id
        self._config = dict()


class VMWarePlatform(Platform):

    def __init__(self, platform_id):
        super(VMWarePlatform, self).__init__(platform_id)
        self.vsphere_interface = None

    @property
    def platform_id(self):
        return self._platform_id

    @property
    def config(self):
        if not self._config:
            self._config = CTX.v2v_pg.query_src_platform(self.platform_id)
        return self._config

    @property
    def platform_type(self):
        return self.config["platform_type"]

    @property
    def name(self):
        return self.config["platform_name"]

    @property
    def ip(self):
        return self.config["platform_ip"]

    @property
    def port(self):
        return self.config["platform_port"]

    @property
    def user(self):
        return self.config["platform_user"]

    @property
    def password(self):
        return self.config["platform_password"]

    @property
    def vm_dir(self):
        return self.config["vm_directory"]

    @property
    def resource(self):
        return self.config["resource"]

    @property
    def status(self):
        """获取虚拟机的状态
        区别于get_vm_status方法，此处的状态是从数据库取"""
        return self.config["status"]

    @connect
    def get_vm_status(self, vm_id):
        """获取虚拟机的状态
        区别于status方法，此处的状态是直接从vmware取的实时状态"""
        try:
            vm = self.vsphere_interface.get_vm_by_uuid(vm_id)
        except Exception as e:
            log_msg = "get vm info from vmware_vsphere failed, platform name: " \
                      "{platform_name}, platform ip: {platform_ip}, vm id: " \
                      "{vm_id}, error reason: {error_reason}".\
                format(platform_name=self.name,
                       platform_ip=self.ip,
                       vm_id=vm_id,
                       error_reason=e)
            logger.error(log_msg)
            raise Exception(log_msg)

        return vm.summary.runtime.powerState
