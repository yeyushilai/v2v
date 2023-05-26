# -*- coding: utf-8 -*-

from pyVmomi import vim

from log.logger import logger
from utils.net import (
    is_reachable,
    is_port_open
)

from fg.resource_control.vmware_vsphere.interface import VMwareVSphereInterface


class VMwareVSphere(object):
    """ VMware vSphere类 """

    def __init__(self, account):
        self.account = account
        self.vi = VMwareVSphereInterface(account)

    def is_connected(self):
        """检查和VMware vSphere平台的连通性
        联通返回True，不连通返回False
        """

        ip = self.account["ip"]
        port = int(self.account["port"])

        # 检查IP是否通达
        if not is_reachable(ip, retries=3):
            logger.error("check network of VMware vSphere failed, ip: {ip}"
                         ", reason: ip is not reachable"
                         "".format(ip=ip))
            return False

        # 检查端口是否通达
        if not is_port_open(ip, port):
            logger.error("check network of VMware vSphere failed, ip: {ip}"
                         ", port: {port}, reason: port is not open"
                         "".format(ip=ip, port=port))
            return False

        # 检测是否联通
        return self.vi.check_connected()

    def list_cluster(self, cluster_name=None):
        result = list()

        if cluster_name:
            cluster = self.vi.get_cluster(cluster_name)
            clusters = [cluster]
        else:
            clusters = self.vi.clusters

        for cluster in clusters:
            temp_dict = dict()
            temp_dict["name"] = cluster.name
            """
            后续视情况返回字段，目前识别到可以返回的字段:
            1.集群的统计信息
            2.集群的网络信息
            3.集群的节点信息
            4.集群的资源池信息
            """
            result.append(temp_dict)
        return result

    def list_vm(self, vm_properties=None):
        """展示平台中的所有的虚拟机"""

        if vm_properties is None:
            vm_properties = [
                "parent",
                "guest.ipAddress",
                "guest.toolsStatus",
                "summary.config.uuid",
                "summary.config.template",
                "summary.config.name",
                "summary.runtime.powerState",
                "summary.config.guestId",
                "summary.config.guestFullName",
                "config.hardware.numCPU",
                "config.hardware.memoryMB",
                "config.annotation"
            ]
            version = self.vi.version
            # 从6.7版本开始，才有创建日期属性
            if "6.7" in version:
                vm_properties.append("config.createDate")
            if "7.0" in version:
                vm_properties.append("config.createDate")
            if "8.0" in version:
                vm_properties.append("config.createDate")

        vms_list = list()
        for vm_data in self.vi.get_vms(vm_properties):
            try:
                vms_list.append(self.vi.layout_dict_vm_data(vm_data))
            except Exception as e:
                uuid = vm_data.get("summary.config.uuid")
                logger.exception("layout data from vm data failed, uuid: "
                                 "{uuid}, reason: {reason}"
                                 "".format(uuid=uuid, reason=e))
                continue
        return vms_list

    def list_datacenter_vm(self, datacenter_name):
        """展示平台中某一个数据中心的虚拟机"""

        vms_data = list()
        for vm_data in self.vi.get_datacenter_vms(datacenter_name):
            try:
                vms_data.append(self.vi.layout_dict_vm_data(vm_data))
            except Exception as e:
                uuid = vm_data.get("summary.config.uuid")
                logger.exception("layout data from vm data failed, uuid: "
                                 "{uuid}, reason: {reason}"
                                 "".format(uuid=uuid, reason=e))
                continue

        return vms_data

    def list_cluster_vm(self, cluster_name):
        """展示平台中某一个集群里的虚拟机"""

        vms_data = list()
        for vm_data in self.vi.get_cluster_vms(cluster_name):
            try:
                vms_data.append(self.vi.layout_dict_vm_data(vm_data))
            except Exception as e:
                uuid = vm_data.get("summary.config.uuid")
                logger.exception("layout data from vm data failed, uuid: "
                                 "{uuid}, reason: {reason}"
                                 "".format(uuid=uuid, reason=e))
                continue

        return vms_data

    def list_resource(self):
        datacenter_list = list()
        for datacenter in self.vi.datacenters:
            dc_dict = dict()
            dc_dict["name"] = datacenter.name
            dc_dict["vm_folder_name"] = datacenter.vmFolder.name
            dc_dict["host_folder_name"] = datacenter.hostFolder.name

            cluster_list = []
            for child in datacenter.hostFolder.childEntity:
                if isinstance(child, vim.ClusterComputeResource):
                    cluster_dict = dict()
                    cluster_dict["name"] = child.name

                    host_list = []
                    for host in child.host:
                        host_dict = dict()
                        host_dict["name"] = host.name
                        host_list.append(host_dict)
                    cluster_dict["host_list"] = host_list
                    cluster_list.append(cluster_dict)

            dc_dict["cluster_list"] = cluster_list
            datacenter_list.append(dc_dict)
        return datacenter_list

    def get_vm(self, vm_name=None, vm_uuid=None, vm_result_q=None):
        if vm_name:
            vm_obj = self.vi.get_vm_by_name(vm_name)
        else:
            vm_obj = self.vi.get_vm_by_uuid(vm_uuid)

        if vm_result_q:
            vm_result_q.put(vm_obj)
        if not vm_obj:
            return vm_obj

        return self.vi.layout_obj_vm_data(vm_obj)

    def update_vm(self, vm_uuid, vm_info):
        return self.vi.update_vm_by_uuid(vm_uuid, vm_info)
