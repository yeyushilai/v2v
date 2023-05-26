# -*- coding: utf-8 -*-

import re

from xmltodict import parse

from log.logger import logger
from utils.id_tool import get_uuid
from utils.json import json_load, json_dump


def catch_exception(func):
    def decor_warp(*args, **kwargs):
        instance = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                "get vm upload image path:%s \n data:%s \nerror: %s" % (
                instance.src_vm_path,
                instance.common_dict, e))
            raise e

    return decor_warp


class VmWareImg(object):
    root_key = "Envelope"
    vsytem_key = "VirtualSystem"
    hardware_key = "VirtualHardwareSection"
    disk_key = "DiskSection"
    rt_key = "rasd:ResourceType"
    os_key = "OperatingSystemSection"

    def __init__(self, xml_data, path):
        self.src_vm_info = None
        self.src_vm_system = None
        self.hardware_info = None
        self.cpu = ''
        self.memory = ''
        self.os_type = ''
        self.os_name = ''
        self.common_dict = None
        self.src_vm_path = path
        self.disk_item = {}
        self.xml_data = xml_data
        self.__parse_xml(xml_data)
        self.disk_data = None

    def __parse_xml(self, xml_data):
        parse_data = parse(xml_data, encoding='utf-8')
        dump_data = json_dump(parse_data, ensure_ascii=False)
        self.common_dict = json_load(dump_data)

    @catch_exception
    def parse_vm_dict(self):
        self.src_vm_info = self.common_dict.get(self.root_key)
        self.src_vm_system = self.src_vm_info.get(self.vsytem_key)
        src_vm_name = self.src_vm_system.get("Name")
        self.hardware_info = self.src_vm_system.get(self.hardware_key)
        self.parse_hardware_info_item()
        self.get_os_type_and_name()
        self.disk_data = self.src_vm_info.get(self.disk_key)
        src_disk = self.build_src_disk_info()
        src_vm_path = 'nfs://' + self.src_vm_path if not self.src_vm_path.startswith(
            "nfs") else self.src_vm_path
        src_vm = {
            "uuid": get_uuid('vm-ova', width=8),
            "template": False,
            "name": src_vm_name,
            "status": 1,
            "path": src_vm_path,
            "os_type": self.os_type,
            "os_name": self.os_name,
            "cpu": int(self.cpu),
            "memory": int(self.memory),
            "disk": src_disk,
        }
        return src_vm

    def build_src_disk_info(self):
        disk_list = list()
        disk_info = self.disk_data.get("Disk")
        if isinstance(disk_info, list):
            for di in disk_info:
                self.process_disk_info(di, disk_list)
        elif isinstance(disk_info, dict):
            self.process_disk_info(disk_info, disk_list)
        return disk_list

    def process_disk_info(self, di, disk_list):
        disk_id = di.get("@ovf:diskId")
        hard_key = self.disk_item.get(disk_id)
        ovf_capacity = di.get("@ovf:capacity")
        ovf_unit = di.get("@ovf:capacityAllocationUnits")

        if ovf_unit == "byte * 2^30":
            # 默认为GB
            src_size = int(round(float(ovf_capacity)))
        elif ovf_unit == "byte * 2^20":
            # MB转换为GB
            src_size = int(round(float(ovf_capacity))) / 1024
        elif ovf_unit == "byte * 2^10":
            # KB转换为GB
            src_size = int(round(float(ovf_capacity))) / 1024 / 1024
        elif ovf_unit == "byte":
            # B转换为GB
            src_size = int(round(float(ovf_capacity))) / 1024 / 1024 / 1024
        else:
            # 默认为GB
            src_size = int(round(float(ovf_capacity)))

        temp_disk_info = {
            "name": hard_key,
            "size": src_size
        }

        disk_list.append(temp_disk_info)

    def parse_hardware_info_item(self):
        system_item = self.hardware_info.get("Item")
        for im in system_item:
            rt = im.get(self.rt_key)
            if rt == "3":
                self.cpu = im.get("rasd:VirtualQuantity")
            elif rt == "4":
                self.memory = im.get("rasd:VirtualQuantity")
            elif rt == "17":
                hard_key = im.get("rasd:ElementName")
                rd_hr = im.get("rasd:HostResource")
                rd_key = ''
                vmdisk = re.findall(r'vmdisk\d', rd_hr)
                if len(vmdisk) > 0:
                    rd_key = vmdisk[0]
                if rd_key:
                    self.disk_item[rd_key] = hard_key
            else:
                continue

    def get_os_type_and_name(self):
        os_info = self.src_vm_system.get(self.os_key)
        self.os_type = os_info.get("@vmw:osType")
        self.os_name = os_info.get("Description")

    @catch_exception
    def get_vmdk_file_count(self):
        refer = self.src_vm_info.get("References")
        files = refer.get("File")
        count = 0
        if isinstance(files, list):
            for s_file in files:
                if s_file.get("@ovf:href") and s_file.get("@ovf:href").endswith(
                        "vmdk"):
                    count += 1
        elif isinstance(files, dict):
            if files.get("@ovf:href") and files.get("@ovf:href").endswith(
                    "vmdk"):
                count += 1
        return count
