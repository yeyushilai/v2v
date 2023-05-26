# -*- coding: utf-8 -*-

from fg.uutils.pg.interface import TableVm
from fg.dto import BaseDto

tb_vm_obj = TableVm()


class VmSession(BaseDto):

    def __init__(self, session_id):
        self.session_id = session_id
        self._config = None

    @property
    def dst_vm_total_disk_size(self):
        total_disk_size = 0
        for d_disk in self.config.get("dst_vm_disk"):
            total_disk_size += d_disk.get("size")
        return total_disk_size

    @property
    def dst_vm_disk(self):
        return self.config["dst_vm_disk"]

    @property
    def dst_vm_os_disk(self):
        return self.config["dst_vm_os_disk"]

    @property
    def dst_vm_data_disk(self):
        return self.config["dst_vm_data_disk"]

    @property
    def dst_vm_image(self):
        return self.config["dst_vm_image"]

    @property
    def dst_vm_cpu_core(self):
        return self.config["dst_vm_cpu_core"]

    @property
    def dst_vm_memory(self):
        return self.config["dst_vm_memory"]

    @property
    def dst_vm_net(self):
        return self.config["dst_vm_net"]

    @property
    def dst_vm_type(self):
        return self.config["dst_vm_type"]

    @property
    def dst_vm_os_name(self):
        return self.config["dst_vm_os_name"]

    @property
    def dst_vm_os_type(self):
        return self.config["dst_vm_os_type"]

    @property
    def config(self):
        if self._config is None:
            self._config = tb_vm_obj.query_vm(self.session_id)
        return self._config

    @config.setter
    def config(self, value):
        self.config.update(value)

    def update_config_to_pg(self, config):
        self.config = config
        condition = dict(session_id=self.session_id)
        return tb_vm_obj.update_vm(condition=condition, columns=config)
