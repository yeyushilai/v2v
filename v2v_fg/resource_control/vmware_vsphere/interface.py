# -*- coding: utf-8 -*-

import ssl
from copy import deepcopy

from pyVmomi import vim

from log.logger import logger

from fg.uutils.utils_common import get_format_datetime, aes_decode
from fg.resource_control.vmware_vsphere.tools import service_instance, pchelper, tasks


# 忽略ssl
ssl._create_default_https_context = ssl._create_unverified_context


class VMwareVSphereInterface(object):
    """ VMware vSphere接口类 """

    def __init__(self, account):
        account_cp = deepcopy(account)

        if not account_cp.get("password"):
            account_cp["password"] = aes_decode(account_cp["encrypt_password"])

        self.account = account_cp
        self._si = None
        self._content = None

    @property
    def si(self):
        if self._si is None:
            self._si = service_instance.connect(self.account)
        return self._si

    @property
    def content(self):
        if self._content is None:
            self._content = self.si.RetrieveContent()
        return self._content

    @property
    def version(self):
        return self.content.about.version

    @property
    def datacenters(self):
        return pchelper.get_all_obj(self.content, [vim.Datacenter])

    @property
    def clusters(self):
        return pchelper.get_all_obj(self.content, [vim.ClusterComputeResource])

    def get_vms(self, vm_properties=None):
        """获取平台中所有的虚拟机"""
        vms_view_ref = pchelper.get_container_view(self.si,
                                                   [vim.VirtualMachine])
        vms_data = pchelper.collect_properties(
            self.si,
            view_ref=vms_view_ref,
            obj_type=vim.VirtualMachine,
            path_set=vm_properties or self._init_vm_properties(),
            include_mors=True)
        return vms_data

    def check_connected(self):
        """检测和VMware vSphere平台是否联通"""
        try:
            si = service_instance.connect(self.account)
        except (Exception, SystemExit) as e:
            logger.error("connect to VMware vSphere failed, ip: {ip}, "
                         "username: {username}, reason: {reason}"
                         "".format(ip=self.account["ip"],
                                   username=self.account["username"],
                                   reason=e))
            return False
        else:
            if not si:
                return False
        return True

    def get_datacenter(self, datacenter_name):
        """通过名称获取单个数据中心对象"""
        return pchelper.get_obj(self.content, [vim.Datacenter], datacenter_name)

    def get_cluster(self, cluster_name):
        """通过名称获取单个集群对象"""
        return pchelper.get_obj(self.content, [vim.ClusterComputeResource],
                                cluster_name)

    def get_vm_by_name(self, vm_name):
        """通过名称获取单个虚拟机对象"""
        return pchelper.get_obj(self.content, [vim.VirtualMachine], vm_name)

    def get_vm_by_uuid(self, vm_uuid):
        """通过UUID获取单个虚拟机对象"""
        return self.content.searchIndex.FindByUuid(None, vm_uuid, True)

    def update_vm_by_uuid(self, vm_uuid, vm_info):
        """通过UUID修改单个虚拟机对象"""
        vm_obj = self.content.searchIndex.FindByUuid(None, vm_uuid, True)
        vm_note = vm_info.get("vm_note")
        vm_name = vm_info.get("vm_name")
        spec = vim.vm.ConfigSpec()
        spec.annotation = vm_note or ""
        if vm_name:
            spec.name = vm_name
        task = vm_obj.ReconfigVM_Task(spec)
        tasks.wait_for_tasks(self.si, [task])
        return None

    def get_cluster_vms(self, cluster_name, vm_properties=None):
        """获取平台中某一个集群里所有的虚拟机"""
        cluster_obj = self.get_cluster(cluster_name)

        vms_view_ref = pchelper.get_container_view(
            self.si, obj_type=[vim.VirtualMachine], container=cluster_obj)
        vms_data = pchelper.collect_properties(
            self.si,
            view_ref=vms_view_ref,
            obj_type=vim.VirtualMachine,
            path_set=vm_properties or self._init_vm_properties(),

            # 是否包括托管对象，必须设置为True的话，返回的结果中才能取obj这个属性
            # 但是会明显加大耗时
            include_mors=True)
        return vms_data

    def get_datacenter_vms(self, datacenter_name, vm_properties=None):
        """获取平台中某一个数据中心里所有的虚拟机"""
        datacenter_obj = self.get_datacenter(datacenter_name)

        vms_view_ref = pchelper.get_container_view(
            self.si,
            obj_type=[vim.VirtualMachine],
            container=datacenter_obj)
        vms_data = pchelper.collect_properties(
            self.si,
            view_ref=vms_view_ref,
            obj_type=vim.VirtualMachine,
            path_set=vm_properties or self._init_vm_properties(),

            # 是否包括托管对象，必须设置为True的话，返回的结果中才能取obj这个属性
            # 但是会明显加大耗时
            include_mors=True)
        return vms_data

    def _init_vm_properties(self):
        vm_properties = [
            "parent",
            "guest.ipAddress",
            "guest.toolsStatus",
            "summary.config.uuid",
            "summary.config.template",
            "summary.runtime.host",
            "summary.config.name",
            "summary.runtime.powerState",
            "summary.config.guestId",
            "summary.config.guestFullName",
            "config.hardware.numCPU",
            "config.hardware.memoryMB",
            "config.hardware.device"
        ]
        version = self.version
        # 从6.7版本开始，才有创建日期属性
        if "6.7" in version:
            vm_properties.append("config.createDate")
        if "7.0" in version:
            vm_properties.append("config.createDate")
        if "8.0" in version:
            vm_properties.append("config.createDate")
        return vm_properties

    def layout_dict_vm_data(self, vm_data):
        vm_obj = vm_data["obj"]

        if isinstance(vm_obj, vim.VirtualApp):
            return

        layout_data = dict()

        # 基本信息
        layout_data["uuid"] = vm_data["summary.config.uuid"]
        layout_data["is_template"] = vm_data["summary.config.template"]  # bool
        layout_data["name"] = vm_data["summary.config.name"]
        layout_data["status"] = vm_data["summary.runtime.powerState"]
        layout_data["vmware_tools_status"] = vm_data["guest.toolsStatus"]
        if vm_data.get("config.annotation"):
            layout_data["note"] = vm_data["config.annotation"]
        else:
            layout_data["note"] = ""

        if vm_data.get("config.createDate"):
            layout_data["create_time"] = get_format_datetime(
                vm_data["config.createDate"])
        else:
            layout_data["create_time"] = ""

        # 所属文件夹
        layout_data["folder"] = self.parse_vm_folder(vm_data["parent"], "")

        # 操作系统
        layout_data["os_type"] = self.parse_vm_os_type(
            vm_data["summary.config.guestId"])
        layout_data["os_name"] = vm_data["summary.config.guestFullName"]

        # CPU、内存、网卡
        layout_data["cpu"] = vm_data["config.hardware.numCPU"]
        layout_data["memory"] = vm_data["config.hardware.memoryMB"]
        layout_data["nic"] = [{"ip": vm_obj.guest.ipAddress or ""}]

        # 磁盘
        if vm_data.get("config.hardware.device"):
            disk_list = list()
            for device in vm_data["config.hardware.device"]:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    temp_disk_dict = dict()
                    label = device.deviceInfo.label
                    size = device.capacityInKB
                    if str(size).endswith("L"):
                        size = size[:-1]
                    temp_disk_dict["size"] = int(
                        size) / 1024 / 1024  # 容量，单位GB
                    temp_disk_dict["name"] = label
                    disk_list.append(temp_disk_dict)
            layout_data["disk"] = disk_list

        # 主机
        if vm_data.get("summary.runtime.host"):
            layout_data["host"] = vm_data["summary.runtime.host"].name

        return layout_data

    def layout_obj_vm_data(self, vm_obj):
        if isinstance(vm_obj, vim.VirtualApp):
            return

        layout_data = dict()

        # 基本信息
        layout_data["uuid"] = vm_obj.summary.config.uuid
        layout_data["is_template"] = vm_obj.summary.config.template  # bool
        layout_data["name"] = vm_obj.summary.config.name
        layout_data["status"] = vm_obj.summary.runtime.powerState
        layout_data["note"] = vm_obj.config.annotation or ""
        layout_data["vmware_tools_status"] = vm_obj.guest.toolsStatus
        try:
            create_time = get_format_datetime(vm_obj.config.createDate)
        except Exception:
            create_time = ""
        layout_data["create_time"] = create_time

        # 所属文件夹
        layout_data["folder"] = self.parse_vm_folder(vm_obj.parent, "")

        # 操作系统
        layout_data["os_type"] = self.parse_vm_os_type(
            vm_obj.summary.config.guestId)
        layout_data["os_name"] = vm_obj.summary.config.guestFullName

        # CPU、内存
        layout_data["cpu"] = vm_obj.config.hardware.numCPU
        layout_data["memory"] = vm_obj.config.hardware.memoryMB

        # 磁盘、网卡
        total_nic_dict = dict()
        for nic in vm_obj.guest.net:
            # todo: 目前感觉必须安装了Vmware Tools才有值，否则为空，待后续继续验证
            key = nic.deviceConfigId
            ip_list = list()
            if nic.ipAddress:
                for ip in nic.ipAddress:
                    ip_list.append(ip)
            total_nic_dict[key] = dict(ip_list=ip_list)  # 网卡网络信息

        disk_list = list()
        nic_list = list()
        for device in vm_obj.config.hardware.device:
            # 磁盘
            if isinstance(device, vim.vm.device.VirtualDisk):
                temp_disk_dict = dict()
                temp_disk_dict["size"] = int(
                    device.capacityInKB) / 1024 / 1024  # 容量，单位GB
                temp_disk_dict[
                    "name"] = device.deviceInfo.label  # eg: Hard disk 1
                disk_list.append(temp_disk_dict)

            # 网卡
            if isinstance(device, (vim.vm.device.VirtualVmxnet3,
                                   vim.vm.device.VirtualE1000e)):
                temp_nic_dict = dict()
                temp_nic_dict["name"] = device.deviceInfo.label
                temp_nic_dict["mac"] = device.macAddress
                temp_nic_dict["status"] = device.connectable.status  # eg: ok
                temp_nic_dict[
                    "is_connect"] = device.connectable.connected  # eg: True
                temp_nic_dict["network"] = device.backing.deviceName
                if isinstance(device, vim.vm.device.VirtualVmxnet3):
                    temp_nic_dict["type"] = "vmxnet3"
                if isinstance(device, vim.vm.device.VirtualE1000e):
                    temp_nic_dict["type"] = "e1000e"
                if device.key in total_nic_dict:
                    temp_nic_dict.update(total_nic_dict[device.key])
                nic_list.append(temp_nic_dict)
        layout_data["disk"] = disk_list
        layout_data["nic"] = nic_list

        # 存储
        datastore_list = []
        for datastore_obj in vm_obj.datastore:
            datastore_info = dict()
            datastore_info["name"] = datastore_obj.name
            datastore_info["type"] = datastore_obj.summary.type

            # 总大小(由Byte转为TB)
            t_size = datastore_obj.summary.capacity
            datastore_info["total_size"] = round(
                t_size / float(1024 * 1024 * 1024 * 1024), 2)

            # 可用大小(由Byte转为TB)
            f_size = datastore_obj.summary.freeSpace
            datastore_info["free_size"] = round(
                f_size / float(1024 * 1024 * 1024 * 1024), 2)
            datastore_list.append(datastore_info)
        layout_data["datastore"] = datastore_list

        # 网络
        network_list = []
        for network_obj in vm_obj.network:
            network_info = dict()
            network_info["name"] = network_obj.name
            network_list.append(network_info)
        layout_data["network"] = network_list

        # 主机
        layout_data["host"] = vm_obj.summary.runtime.host.name

        # 集群
        layout_data["cluster"] = vm_obj.summary.runtime.host.parent.name
        return layout_data

    @staticmethod
    def parse_vm_os_type(os_guest_type):
        """解析虚拟机类型"""
        if os_guest_type.lower().startswith(
                ("windows", "winxp", "winNet", "win")):
            vm_type = "windows"
        elif os_guest_type.lower().startswith('centos'):
            vm_type = 'centos'
        elif os_guest_type.lower().startswith('debian'):
            vm_type = 'debian'
        elif os_guest_type.lower().startswith('ubuntu'):
            vm_type = 'ubuntu'
        elif os_guest_type.lower().startswith(('suse', 'sles')):
            vm_type = 'suse'
        elif os_guest_type.lower().startswith('rhel'):
            vm_type = 'redhat'
        elif os_guest_type.lower().startswith('opensuse'):
            vm_type = 'opensuse'
        elif os_guest_type.lower().startswith('coreos'):
            vm_type = 'coreos'
        elif os_guest_type.lower().startswith('fedora'):
            vm_type = 'fedora'
        elif os_guest_type.lower().startswith('desktop'):
            vm_type = 'desktop'
        elif os_guest_type.lower().startswith('freebsd'):
            vm_type = 'freebsd'
        elif os_guest_type.lower().startswith('arch'):
            vm_type = 'arch'
        elif os_guest_type.lower().startswith('oracle'):
            vm_type = 'oracle'
        else:
            vm_type = ""

        return vm_type

    def parse_vm_folder(self, parent_obj, path):
        """解析虚拟机的路径"""

        if parent_obj.name == "vm":
            # if path.endswith("/"):
            #     path = path[:-1]
            tmp_path = path
        else:
            tmp_path = parent_obj.name + "/" + path
            parent_obj = parent_obj.parent
            tmp_path = self.parse_vm_folder(parent_obj, tmp_path)

        return tmp_path
