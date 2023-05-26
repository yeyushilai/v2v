# -*- coding: utf-8 -*-

import ssl
from copy import deepcopy

from pyVmomi import vim

from uutils.common import aes_decode
from resource_control.vmware_vsphere.tools import service_instance
from resource_control.vmware_vsphere.tools import pchelper
from uutils.time_utils import get_format_datetime
from constants.vmware_vsphere import TIMEOUT_CONNECT_TO_VMWARE_VSPHERE
from constants.vmware_vsphere import SrcPlatformNotConnectReason

# 忽略ssl
ssl._create_default_https_context = ssl._create_unverified_context


class VsphereInterface(object):
    """vsphere接口类"""

    def __init__(self, account):
        account_copy = deepcopy(account)
        if not account_copy.get("password"):
            account_copy["password"] = aes_decode(account_copy["encrypt_password"])

        self.account = account_copy
        self.account["timeout"] = TIMEOUT_CONNECT_TO_VMWARE_VSPHERE
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

    def get_version(self):
        return self.content.about.version

    def list_datacenter(self):
        return pchelper.get_all_obj(self.content, [vim.Datacenter])

    def check_connect(self):
        """检查和vsphere的连通性"""
        res = dict(is_connect=True, err_msg="")
        try:
            self.list_datacenter()
        except Exception as e:
            res["is_connect"] = False
            res["err_msg"] = str(e)
            res["err_reason"] = SrcPlatformNotConnectReason.COMMON_ERROR.value
        return res

    def get_cluster(self, cluster_name):
        """获取单个集群中的信息"""
        return pchelper.get_obj(self.content, [vim.ClusterComputeResource],
                                cluster_name)

    def get_vm_by_name(self, vm_name):
        """通过虚拟机名称获取虚拟机的信息"""
        return pchelper.get_obj(self.content, [vim.VirtualMachine], vm_name)

    def get_vm_by_uuid(self, vm_uuid):
        """通过虚拟机UUID获取虚拟机的信息"""
        vm = None
        if self.content:
            vm = self.content.searchIndex.FindByUuid(None, vm_uuid, True)
            if not vm:
                raise Exception('vm is not found, uuid: {uuid}'.format(uuid=vm_uuid))
        return vm

    def get_all_vms(self, vm_properties=None):
        if vm_properties is None:
            vm_properties = list()

        vms_view_ref = pchelper.get_container_view(
            self.si, obj_type=[vim.VirtualMachine])
        vms_data = pchelper.collect_properties(
            self.si,
            view_ref=vms_view_ref,
            obj_type=vim.VirtualMachine,
            path_set=vm_properties,
            include_mors=True)
        return vms_data

    def get_cluster_vms(self, cluster_name, vm_properties=None):
        if vm_properties is None:
            vm_properties = list()
        cluster_obj = self.get_cluster(cluster_name)
        vms_view_ref = pchelper.get_container_view(
            self.si, obj_type=[vim.VirtualMachine], container=cluster_obj)
        vms_data = pchelper.collect_properties(
            self.si,
            view_ref=vms_view_ref,
            obj_type=vim.VirtualMachine,
            path_set=vm_properties,
            include_mors=True)
        return vms_data

    def list_vm_in_cluster(self, cluster_name):
        """展示集群中的虚拟机"""
        vm_properties = ["parent",
                         "summary.config.uuid",
                         # "guest.ipAddress"
                         "summary.runtime.host",
                         "summary.config.name",
                         "summary.runtime.powerState",
                         "summary.config.guestId",
                         "summary.config.guestFullName",
                         "config.hardware.numCPU",
                         "config.hardware.memoryMB",
                         "config.hardware.device",
                         "summary.config.template"]

        version = self.get_version()
        if "6.7" in version:
            vm_properties.append("config.createDate")
        if "7.0" in version:
            vm_properties.append("config.createDate")

        vms_data = self.get_cluster_vms(cluster_name, vm_properties)

        vms = list()
        for vm_data in vms_data:
            vm_obj = vm_data["obj"]
            # vApp不支持迁移
            if isinstance(vm_obj, vim.VirtualApp):
                continue

            temp_vm_data = dict()

            # ID、主机、名称，状态，创建时间
            temp_vm_data["uuid"] = vm_data["summary.config.uuid"]
            temp_vm_data["template"] = vm_data["summary.config.template"]  # True或者False
            temp_vm_data["host"] = vm_data["summary.runtime.host"].name
            temp_vm_data["name"] = vm_data["summary.config.name"]
            temp_vm_data["status"] = vm_data["summary.runtime.powerState"]

            # 创建日期
            if vm_data.get("config.createDate"):
                create_time = get_format_datetime(vm_data["config.createDate"])
            else:
                create_time = ""
            temp_vm_data["create_time"] = create_time

            # 所属文件夹
            temp_vm_data["folder"] = get_vm_folder(vm_data["parent"], "")

            # 操作系统
            temp_vm_data["os_type"] = parse_vm_type(
                vm_data["summary.config.guestId"])
            temp_vm_data["os_name"] = vm_data[
                "summary.config.guestFullName"]

            # CPU、内存、网卡
            temp_vm_data["cpu"] = vm_data["config.hardware.numCPU"]
            temp_vm_data["memory"] = vm_data["config.hardware.memoryMB"]
            # temp_vm_data["net"] = [{"ip": vm_obj.guest.ipAddress or ""}]
            temp_vm_data["net"] = [{"ip": ""}]

            # 磁盘
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
            temp_vm_data["disk"] = disk_list

            vms.append(temp_vm_data)

        return vms


def parse_vm_type(os_guest_type):
    """解析虚拟机类型"""
    if os_guest_type.lower().startswith(("windows", "winxp", "winNet", "win")):
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


def get_vm_folder(parent_obj, path):
    """获取虚拟机的路径"""

    if parent_obj.name == "vm":
        # if path.endswith("/"):
        #     path = path[:-1]
        tmp_path = path
    else:
        tmp_path = parent_obj.name + "/" + path
        parent_obj = parent_obj.parent
        tmp_path = get_vm_folder(parent_obj, tmp_path)

    return tmp_path
