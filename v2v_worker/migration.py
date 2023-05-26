# -*- coding: utf-8 -*-

"""
功能：迁移

功能分解：
1.导出镜像/上传镜像
2.处理镜像
3.创建虚拟机
4.覆盖镜像
5.修复调优
"""

import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import datetime
import shutil
import tarfile
import time

from log.logger import logger

from utils.misc import get_current_time
from api.constants import (
    INST_TRAN_STATUS_STARTING,  # starting
    INST_STATUS_STOP,  # stopped
    INST_STATUS_RUN,  # running
)

from resource_control.nas.interface import NFSInterface
from resource_control.nas.tool import copy_nfs_file
from uutils.xml_convertor import xml_file_to_json_file
from uutils.pg.tool import wait_job_successful
from uutils.time_utils import now_local_format
from uutils.nbd.tool import (
    # 映射nbd设备
    map_nbd_device_context,

    # 挂载nbd设备
    mount_nbd_device_context
)

from uutils.qbd.tool import (
    # 映射qbd设备
    map_qbd_device_context,

    # 挂载qbd设备
    # mount_qbd_device_context
)

from uutils.common import (
    normal_exec,
    bash_exec,
    aes_decode,
    read_file,
    sha256_tool,
    find_file,
    get_file_size
)

from constants.template import (
    # 通用模板
    SSH_CMD_OPTION,
    SSH_CMD_TEMPLATE,
    SCP_CMD_TEMPLATE,

    # 导出镜像
    EXPORT_IMAGE_CMD_TEMPLATE,

    # 处理镜像
    DEAL_IMAGE_CONVERT_IMAGE_CMD_TEMPLATE,

    # 创建虚拟机
    CREATE_INSTANCE_INSERT_IMAGE_TEMPLATE
)

from constants.common import (
    # 迁移相关
    RunningDetailMigrateStatus,
    MigrateStatus,
    MigratePattern,

    # 导出镜像
    EXPORT_IMAGE_TIMEOUT,
    EXPORT_IMAGE_MAX_RETRY_TIMES,
    EXPORT_IMAGE_CMD_VI_PREFIX,
    EXPORT_IMAGE_DEFAULT_PARAMS,
    EXPORT_IMAGE_DST_FORMAT_OVA,

    # 上传镜像
    UPLOAD_IMAGE_TIMEOUT,

    # 处理镜像
    DEAL_IMAGE_SRC_FORMAT_VMDK,
    DEAL_IMAGE_DST_FORMAT_QCOW2,
    DEAL_IMAGE_CONVERT_IMAGE_TIMEOUT,

    # 创建虚拟机
    CREATE_INSTANCE_IMAGE_FILE_PATH,
    CREATE_INSTANCE_RUN_INSTANCE_TIMEOUT,
    CREATE_INSTANCE_START_INSTANCE_TIMEOUT,
    CREATE_INSTANCE_RESTART_INSTANCE_TIMEOUT,
    CREATE_INSTANCE_STOP_INSTANCE_TIMEOUT,
    CREATE_INSTANCE_CREATE_VOLUMES_TIMEOUT,
    CREATE_INSTANCE_ATTACH_VOLUMES_TIMEOUT,

    # 覆盖镜像
    COVER_IMAGE_TIMEOUT
)

# 青云云平台相关
from constants.iaas import (
    QemuImgAction,

    # hyper节点相关常量
    HYPER_IMAGE_BASE_DIR,
    HYPER_VMWARE_OVF_TOOL_PATH,
    HYPER_QEMU_IMG_TOOL_PATH,
    HyperContainerMode,

    # seed节点相关常量
    SEED_NODES,
    SEED_IMAGE_REPOSITORY_BASE_DIR,
    SEED_ID_RSA_PATH,
    SEED_DEFAULT_USER
)

# 青云云平台上面的虚拟机
from constants.iaas import (
    # 镜像
    ImageStatus,

    # 虚拟机
    InstanceOSType,
    INSTANCE_BOOT_LOADER_MAPPER,

    # 卷（硬盘）
    # LocalVolumeType,
    # SupportVolumeType,
    SANCVolumeType

)
from constants.error import ErrorMsg, ErrorCode
from context import WorkerContext


class BaseMigration(object):
    ctx = WorkerContext()

    def __init__(self, vm_session):
        self.vm_session = vm_session
        self.ovf_path = ""
        self.vmdk_path_list = list()

    def migrate(self):
        """开始迁移"""

        # 记录开始时间
        start_time = datetime.datetime.now()
        try:
            self.export_image()  # Note:只有导出镜像模式迁移才有此步骤
            self.upload_image()  # Note:只有上传镜像模式迁移才有此步骤
            self.deal_image()
            self.create_vm()
            self.cover_image()
            self.recorrect_and_optimize()
        except Exception as e:
            # 更新状态
            detail_status = dict(status=MigrateStatus.FAILED.value)
            if not self.vm_session.err_msg:
                detail_status["err_msg"] = ErrorMsg.ERROR_COMMON.value.zh
            if not self.vm_session.err_code:
                detail_status["err_code"] = ErrorCode.ERROR_COMMON.value
            self.vm_session.update_detail_migrate_status(detail_status)
            log_msg = "vm has migrated failed, session id: {session_id}, error" \
                      " reason: {error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                error_reason=str(e))
            logger.error(log_msg)
            logger.exception(e)
            raise Exception(log_msg)

        # 记录结束时间并统计
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        time_strftime = str(datetime.timedelta(seconds=total_seconds))
        logger.info("vm has migrated successfully, session id: "
                    "{session_id}, cost time: {cost_time}"
                    .format(session_id=self.vm_session.session_id,
                            cost_time=time_strftime))

    def export_image(self):
        pass

    def upload_image(self):
        pass

    def deal_image(self):
        """处理镜像
        包括：
        1.解压镜像  Note:只有导出镜像模式迁移才有此步骤
        2.检查镜像  Note:只有导出镜像模式迁移才有此步骤
        3.生成目标虚拟机磁盘信息
        4.转换镜像格式
        """
        logger.info("deal image start, session id: {session_id}"
                    .format(session_id=self.vm_session.session_id))
        # 更新详细的迁移状态信息
        start_status = RunningDetailMigrateStatus.START_DEAL_IMAGE_DETAIL_STATUS.value
        start_status["step"]["start_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(start_status)

        # 1.解压镜像
        self._uncompress_image()

        # # 2.检查镜像
        # self._check_image()

        # 3.生成目标虚拟机磁盘信息
        self._gen_dst_vm_disk_info()

        # 4.转换镜像格式
        self._convert_image()

        # 更新详细的迁移状态信息
        end_status = RunningDetailMigrateStatus.END_DEAL_IMAGE_DETAIL_STATUS.value
        end_status["step"]["end_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(end_status)
        logger.info("deal image end, session id: {session_id}"
                    .format(session_id=self.vm_session.session_id))

    def create_vm(self):
        """创建虚拟机"""
        logger.info("create dst vm start, user id: {user_id}, session id: "
                    "{session_id}"
                    .format(session_id=self.vm_session.session_id,
                            user_id=self.vm_session.user_id))
        # 更新详细的迁移状态信息
        start_status = RunningDetailMigrateStatus.START_CREATE_INSTANCE_DETAIL_STATUS.value
        start_status["step"]["start_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(start_status)

        # 1.插入镜像数据
        self._insert_image()

        # 2.更新镜像资源计费信息
        # self._update_resource_leasing()

        # 3.拷贝空镜像到seed节点
        self._copy_image_to_seed()

        # 4.创建目标虚拟机
        self._create_dst_vm()

        # # 5.关闭目标虚拟机
        self._stop_dst_vm()

        # 6.更新目标虚拟机镜像的状态为弃用
        self._update_dst_vm_image_status()

        # 7.从seed节点删除空镜像 （这个的风险未知，因此暂时不清理）
        # self._delete_image_from_seed()

        # 8.创建目标虚拟机的系统盘
        self._create_dst_vm_disks()

        # 9.加载目标虚拟机的系统盘
        self._attach_dst_vm_disks()

        # 更新详细的迁移状态信息
        end_status = RunningDetailMigrateStatus.END_CREATE_INSTANCE_DETAIL_STATUS.value
        end_status["step"]["end_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(end_status)
        logger.info("create dst vm end, user id: {user_id}, session id: "
                    "{session_id}, image id: {image_id}, dst vm id: {dst_vm_id}"
                    .format(session_id=self.vm_session.session_id,
                            user_id=self.vm_session.user_id,
                            image_id=self.vm_session.dst_vm_image,
                            dst_vm_id=self.vm_session.dst_vm_id))

    def cover_image(self):
        """覆盖镜像"""
        logger.info("cover image start, session id: {session_id}"
                    "".format(session_id=self.vm_session.session_id))

        # 更新详细的迁移状态信息
        start_status = RunningDetailMigrateStatus.START_COVER_IMAGE_DETAIL_STATUS.value
        start_status["step"]["start_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(start_status)

        if self.ctx.local_node.container_mode == HyperContainerMode.SANC.value:
            # 启动目标虚拟机
            self._start_dst_vm()

            # 使用mv, 覆盖系统盘
            self._cover_image_by_move(self.vm_session.dst_vm_os_disk)

            # 使用dd，覆盖数据盘
            for disk_info in self.vm_session.dst_vm_data_disk:
                self._cover_image_by_dd(disk_info)

            # 重启目标虚拟机
            self._restart_dst_vm()
        else:
            # 使用mv，覆盖所有的硬盘数据（包括系统盘和数据盘）
            for disk_info in self.vm_session.dst_vm_disk:
                self._cover_image_by_move(disk_info)

            # 启动虚拟机
            self._start_dst_vm()

        # 更新详细的迁移状态信息
        end_status = RunningDetailMigrateStatus.END_COVER_IMAGE_DETAIL_STATUS.value
        end_status["step"]["end_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(end_status)
        logger.info("cover image end, session id: {session_id}"
                    "".format(session_id=self.vm_session.session_id))

    def recorrect_and_optimize(self):
        """修复调优"""
        logger.info("recorrect and optimize start, session id: {session_id}"
                    .format(session_id=self.vm_session.session_id))
        # 更新详细的迁移状态信息
        start_status = RunningDetailMigrateStatus.START_RECORRECT_AND_OPTIMIZE_DETAIL_STATUS.value
        start_status["step"]["start_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(start_status)

        # 1.修复目标虚拟机驱动问题
        self._patch_drive()

        # 2.上传代理到目标虚拟机
        self._upload_proxy()

        # 更新详细的迁移状态信息
        end_status = RunningDetailMigrateStatus.END_RECORRECT_AND_OPTIMIZE_DETAIL_STATUS.value
        end_status["step"]["end_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(end_status)
        logger.info("recorrect and optimize end, session id: {session_id}"
                    .format(session_id=self.vm_session.session_id))

    def _uncompress_image(self):
        pass

    def _check_image(self):
        pass

    def _gen_dst_vm_disk_info(self):
        """生成目标虚拟机磁盘信息"""
        logger.info("generate dst vm disk info start, session id: "
                    "{session_id}"
                    .format(session_id=self.vm_session.session_id))

        self.json_path = self.ovf_path.replace("ovf", "json")
        ovf_config = xml_file_to_json_file(self.ovf_path, self.json_path)

        Envelope = ovf_config["Envelope"]

        # disk_id和disk_label的映射
        # example
        # {
        #   "vmdisk1": "Hard disk 1",
        #   "vmdisk2": "Hard disk 2"
        # }
        VirtualSystem = Envelope["VirtualSystem"]
        VirtualHardwareSection = VirtualSystem["VirtualHardwareSection"]
        Item = VirtualHardwareSection["Item"]
        disk_id_disk_label_mapper = dict()
        for item in Item:
            if "rasd:HostResource" in item.keys():
                HostResource = item[
                    "rasd:HostResource"]  # eg: "ovf:/disk/vmdisk1"
                resource = HostResource.split("/")[-1]  # eg: "vmdisk1"
                ElementName = item["rasd:ElementName"]  # eg: "Hard disk 1"
                disk_id_disk_label_mapper[resource] = ElementName
        logger.info(
            "disk id and disk label mapper: {disk_id_disk_label_mapper}, "
            "session id: {session_id}, src vm id: {src_vm_id}"
            .format(session_id=self.vm_session.session_id,
                    src_vm_id=self.vm_session.src_vm_id,
                    disk_id_disk_label_mapper=disk_id_disk_label_mapper))

        # file_ref和disk_attr的映射
        # example:
        # {
        #     "file1": {
        #         "ovf_disk_id": "vmdisk1",
        #         "ovf_capacity": 100,
        #         "ovf_unit": "byte * 2^30",
        #     },
        #     "file2": {
        #         "ovf_disk_id": "vmdisk2",
        #         "ovf_capacity": 100,
        #         "ovf_unit": "byte * 2^30",
        #     }
        # }
        DiskSection = Envelope["DiskSection"]
        DiskSectionInfo = DiskSection["Disk"]
        file_ref_disk_attr_map = dict()
        # 若源虚拟机有单个硬盘
        if isinstance(DiskSectionInfo, dict):
            ovf_file_ref = DiskSectionInfo["@ovf:fileRef"]  # eg: "file1"
            ovf_disk_id = DiskSectionInfo["@ovf:diskId"]  # eg: "vmdisk1"
            ovf_capacity = DiskSectionInfo["@ovf:capacity"]  # eg: 100
            ovf_unit = DiskSectionInfo[
                "@ovf:capacityAllocationUnits"]  # byte * 2^30
            file_ref_disk_attr_map[ovf_file_ref] = dict(
                ovf_disk_id=ovf_disk_id,
                ovf_capacity=ovf_capacity,
                ovf_unit=ovf_unit)
        # 若源虚拟机有多个硬盘
        elif isinstance(DiskSectionInfo, list):
            for section in DiskSectionInfo:
                ovf_file_ref = section["@ovf:fileRef"]  # eg: "file1"
                ovf_disk_id = section["@ovf:diskId"]  # eg: "vmdisk1"
                ovf_capacity = section["@ovf:capacity"]  # eg: 100
                ovf_unit = section[
                    "@ovf:capacityAllocationUnits"]  # byte * 2^30
                file_ref_disk_attr_map[ovf_file_ref] = dict(
                    ovf_disk_id=ovf_disk_id,
                    ovf_capacity=ovf_capacity,
                    ovf_unit=ovf_unit)
        logger.info("file ref and disk attr mapper: "
                    "{file_ref_disk_attr_map}, session id: {session_id}, "
                    "src vm id: {src_vm_id}"
                    .format(session_id=self.vm_session.session_id,
                            src_vm_id=self.vm_session.src_vm_id,
                            file_ref_disk_attr_map=file_ref_disk_attr_map))

        # ovf_href和ovf_id的映射
        # example
        # {
        #   "xxxx-disk1.vmdk": "file1",
        #   "xxxx-disk2.vmdk": "file2"
        # }
        ovf_href_ovf_id_mapper = dict()
        References = Envelope["References"]
        File = References["File"]
        # 若源虚拟机有单个硬盘
        if isinstance(File, dict):
            ovf_id = File["@ovf:id"]  # eg: "file1"
            ovf_href = File["@ovf:href"]  # eg: "xxxx-disk1.vmdk""
            ovf_href_ovf_id_mapper[ovf_href] = ovf_id
        # 若源虚拟机有多个硬盘
        elif isinstance(File, list):
            for file_data in File:
                ovf_id = file_data["@ovf:id"]  # eg: "file1"
                ovf_href = file_data["@ovf:href"]  # eg: "xxxx-disk1.vmdk""
                ovf_href_ovf_id_mapper[ovf_href] = ovf_id
        logger.info("ovf href and ovf id mapper: {ovf_href_ovf_id_mapper}, "
                    "session id: {session_id}, src vm id: {src_vm_id}"
                    .format(session_id=self.vm_session.session_id,
                            src_vm_id=self.vm_session.src_vm_id,
                            ovf_href_ovf_id_mapper=ovf_href_ovf_id_mapper))

        # vmdk文件名称和vmdk文件路径的映射
        # example:
        # {
        #   'xxxx-disk1.vmdk': '/xxxx/v2v_export/session-xxxx/xxxx/xxxx-disk1.vmdk',
        #   'xxxx-disk2.vmdk': '/xxxx/v2v_export/session-xxxx/xxxx/xxxx-disk2.vmdk'
        # }
        dst_vm_disk = list()
        try:
            for vmdk_path in self.vmdk_path_list:
                disk_info = dict()
                decode_vmdk_name = os.path.basename(vmdk_path).decode("utf8")
                decode_vmdk_path = vmdk_path.decode("utf8")
                ovf_id = ovf_href_ovf_id_mapper[decode_vmdk_name]
                ovf_disk_id = file_ref_disk_attr_map[ovf_id]["ovf_disk_id"]
                ovf_capacity = file_ref_disk_attr_map[ovf_id]["ovf_capacity"]
                ovf_unit = file_ref_disk_attr_map[ovf_id]["ovf_unit"]
                disk_label = disk_id_disk_label_mapper[ovf_disk_id]

                disk_info["vmdk_name"] = decode_vmdk_name  # xxxx-disk1.vmdk
                disk_info[
                    "vmdk_path"] = decode_vmdk_path  # /xxxx/v2v_export/session-xxxx/xxxx/xxxx-disk1.vmdk
                disk_info["vmdk_size"] = get_file_size(
                    decode_vmdk_path)  # 单位MB
                disk_info["ovf_id"] = ovf_id  # file1
                disk_info["ovf_disk_id"] = ovf_disk_id  # vmdisk1
                disk_info["name"] = disk_label  # Hard disk 1
                disk_info["name"] = disk_label  # Hard disk 1

                # 容量单位转换
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
                    src_size = int(
                        round(float(ovf_capacity))) / 1024 / 1024 / 1024
                else:
                    # 默认为GB
                    src_size = int(round(float(ovf_capacity)))

                # 容量为10的倍数处理
                src_size_suffix = int(str(src_size)[-1])
                if src_size_suffix == 0:
                    disk_info["size"] = src_size  # 100GB
                else:
                    disk_info["size"] = int(src_size) + (
                                10 - src_size_suffix)  # 100GB

                dst_vm_disk.append(disk_info)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.DEAL_IMAGE_ERROR_DISK_CONFIG_RELATE_IMAGE_PATH.value,
                err_msg=ErrorMsg.DEAL_IMAGE_ERROR_DISK_CONFIG_RELATE_IMAGE_PATH.value.zh))

            log_msg = "generate dst vm disk info failed, session id: " \
                      "{session_id}, dst vm disk: {dst_vm_disk}, error reason" \
                      ": {error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                dst_vm_disk=dst_vm_disk,
                                error_reason=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)

        # 更新配置到数据库
        self.vm_session.update_to_mem_and_pg(dict(dst_vm_disk=dst_vm_disk))
        logger.info("generate dst vm disk info end, session id: "
                    "{session_id}, dst vm disk: {dst_vm_disk}"
                    .format(session_id=self.vm_session.session_id,
                            dst_vm_disk=dst_vm_disk))

    def _convert_image(self):
        """转换镜像"""
        logger.info("convert image start, session id: {session_id}, dst vm "
                    "disk: {dst_vm_disk}"
                    .format(session_id=self.vm_session.session_id,
                            dst_vm_disk=self.vm_session.dst_vm_disk))

        dst_vm_disk = self.vm_session.dst_vm_disk
        for disk_info in dst_vm_disk:
            # 记录开始时间
            start_time = datetime.datetime.now()

            vmdk_path = disk_info["vmdk_path"]
            vmdk_size = disk_info["vmdk_size"]
            disk_info["qcow2_path"] = qcow2_path = vmdk_path.replace("vmdk",
                                                                     "qcow2")

            # 执行转换镜像命令
            convert_cmd = DEAL_IMAGE_CONVERT_IMAGE_CMD_TEMPLATE.format(
                qemu_img_path=HYPER_QEMU_IMG_TOOL_PATH,
                qemu_img_action=QemuImgAction.CONVERT.value,
                src_image_format=DEAL_IMAGE_SRC_FORMAT_VMDK,
                dst_image_format=DEAL_IMAGE_DST_FORMAT_QCOW2,
                src_image_path=vmdk_path,
                dst_image_path=qcow2_path)
            logger.info("convert image ready, session id: {session_id}, disk "
                        "name: {disk_name}, convert cmd: {convert_cmd}"
                        .format(disk_name=disk_info["name"],
                                session_id=self.vm_session.session_id,
                                convert_cmd=convert_cmd))
            returncode, _, stderr = bash_exec(convert_cmd,
                                              DEAL_IMAGE_CONVERT_IMAGE_TIMEOUT)
            if returncode != 0:
                self.vm_session.update_detail_migrate_status(dict(
                    err_code=ErrorCode.CONVERT_IMAGE_ERROR_COMMON.value,
                    err_msg=ErrorMsg.CONVERT_IMAGE_ERROR_COMMON.value.zh))
                log_msg = "convert image failed, session id: {session_id}, " \
                          "disk name: {disk_name}, convert cmd: {convert_cmd}" \
                          ", error reason: {error_reason}" \
                          "".format(disk_name=disk_info["name"],
                                    session_id=self.vm_session.session_id,
                                    convert_cmd=convert_cmd,
                                    error_reason=stderr)
                logger.error(log_msg)
                raise Exception(log_msg)

            # 删掉原始的vmdk文件，节省空间
            disk_info["qcow2_size"] = get_file_size(qcow2_path)
            os.remove(vmdk_path)

            # 统计信息
            end_time = datetime.datetime.now()
            total_seconds = (end_time - start_time).total_seconds()
            logger.info("convert image successfully, session id: {session_id},"
                        " cost time: {cost_time}, vmdk size: {vmdk_size}MB, "
                        "vmdk path: {vmdk_path}, convert speed: "
                        "{convert_speed}MB/s, qcow2 path: {qcow2_path},"
                        .format(
                cost_time=str(datetime.timedelta(seconds=total_seconds)),
                disk_label=disk_info["name"],
                session_id=self.vm_session.session_id,
                qcow2_path=qcow2_path,
                vmdk_path=vmdk_path,
                vmdk_size=vmdk_size,

                # 单位: MB/s
                convert_speed=vmdk_size / total_seconds))

            # 识别系统盘并赋值
            is_os_disk = disk_info.get("is_os_disk",
                                       None) or self.identify_src_vm_os_disk(
                qcow2_path)
            disk_info["is_os_disk"] = is_os_disk
            if is_os_disk:
                disk_info["volume_type"] = \
                self.vm_session.info["dst_vm_os_disk"]["type"]
            else:
                if "dst_vm_data_disk" in self.vm_session.info \
                        and isinstance(
                    self.vm_session.info["dst_vm_data_disk"], dict) \
                        and "type" in self.vm_session.info["dst_vm_data_disk"]:
                    data_disk_type = self.vm_session.info["dst_vm_data_disk"][
                        "type"]
                    disk_info["volume_type"] = data_disk_type

                # IAAS要求：
                # 企业级分布式云盘 (NeonSAN)，编号为5，SAN容量型云盘，编号为6
                # 作为数据盘使用时，最小容量不能低于100GB，步长值为100GB
                if disk_info["volume_type"] in SANCVolumeType.list_type():
                    if disk_info["size"] < 100:
                        disk_info["size"] = 100

                    if disk_info["size"] > 100:
                        src_disk_size_suffix = int(str(disk_info["size"])[-2:])
                        if src_disk_size_suffix == 0:
                            disk_info["size"] = disk_info["size"]  # 100GB
                        else:
                            disk_info["size"] = int(disk_info["size"]) + (
                                        100 - src_disk_size_suffix)  # 100GB

            # 更新虚拟机的配置
            self.vm_session.update_to_pg(dict(dst_vm_disk=dst_vm_disk))

        # 若源虚拟机没有安装系统，则直接报错，迁移终止
        os_disk_tag_list = [disk_info["is_os_disk"] for disk_info in
                            dst_vm_disk]
        if not any(os_disk_tag_list):
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CONVERT_IMAGE_ERROR_OS_DISK_NOT_EXISTS.value,
                err_msg=ErrorMsg.CONVERT_IMAGE_ERROR_OS_DISK_NOT_EXISTS.value.zh))
            log_msg = "there is not a os disk in vm, migrate is not supported," \
                      " session id:{session_id}, dst vm disk {dst_vm_disk}" \
                      "".format(session_id=self.vm_session.session_id,
                                dst_vm_disk=dst_vm_disk)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 若源虚拟机识别错误识别出来多个系统盘，则直接报错，迁移终止
        if len([res for res in os_disk_tag_list if res]) > 1:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CONVERT_IMAGE_ERROR_MULTI_OS_DISK_EXISTS.value,
                err_msg=ErrorMsg.CONVERT_IMAGE_ERROR_MULTI_OS_DISK_EXISTS.value.zh))
            log_msg = "there is multi os disk in vm, migrate is not supported," \
                      " session id:{session_id}, dst vm disk {dst_vm_disk}" \
                      "".format(session_id=self.vm_session.session_id,
                                dst_vm_disk=dst_vm_disk)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 更新虚拟机的配置
        self.vm_session.update_to_pg(dict(dst_vm_disk=dst_vm_disk))
        logger.info("convert image end, session id: {session_id}"
                    .format(session_id=self.vm_session.session_id))

    def _insert_image(self):
        """插入镜像数据"""
        dst_vm_image = self.vm_session.dst_vm_image
        image_id = self.vm_session.dst_vm_image_id
        logger.info("insert image start, session id: {session_id}, dst vm "
                    "image id: {image_id}"
                    "".format(session_id=self.vm_session.session_id,
                              image_id=image_id))

        image_info = CREATE_INSTANCE_INSERT_IMAGE_TEMPLATE
        image_info["base_id"] = image_id
        image_info["root_id"] = image_id
        image_info["image_id"] = image_id
        image_info["billing_id"] = image_id

        # 镜像提供者ID
        image_info["owner"] = self.vm_session.task.owner_id

        image_info["image_name"] = self.vm_session.dst_vm_name
        # 镜像空间大小，单位为 GB
        image_info["size"] = self.vm_session.dst_vm_os_disk["size"]
        image_info["console_id"] = self.vm_session.task.console_id

        image_info["root_user_id"] = self.vm_session.task.owner_id
        image_info["block_bus"] = dst_vm_image["block_bus"]
        image_info["nic_type"] = dst_vm_image["nic_type"]
        image_info["boot_loader"] = INSTANCE_BOOT_LOADER_MAPPER[
            dst_vm_image.get("boot_loader", "auto")]

        # 定义操作系统、用户、密码
        dst_vm_os_type = self.vm_session.dst_vm_os_type

        # 镜像操作系统发行版，有效值为 centos，ubuntu，debian，fedora 和 windows 等
        image_info["os_family"] = dst_vm_os_type
        if dst_vm_os_type.lower() == InstanceOSType.WINDOWS.value:
            # 镜像操作系统平台，有效值为 linux 和 windows
            image_info["platform"] = "windows"
            image_info["default_user"] = "administrator"
            image_info["default_passwd"] = "default"
        elif dst_vm_os_type.lower() in InstanceOSType.list_linux_type():
            image_info["platform"] = "linux"
            image_info["default_user"] = "root"
            image_info["default_passwd"] = "default"
        else:
            err_msg = ErrorMsg.REGISTER_IMAGE_ERROR_UNKNOWN_VM_TYPE.value
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.REGISTER_IMAGE_ERROR_UNKNOWN_VM_TYPE.value,
                err_msg=err_msg.zh))

            log_msg = "insert image failed, session id: {session_id}, " \
                      "dst vm os type: {dst_vm_os_type}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                dst_vm_os_type=dst_vm_os_type,
                                error_reason=err_msg.en)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 先清除数据库记录，再插入数据库记录
        logger.info("insert image ready, session id: {session_id}, image_id: "
                    "{image_id}, image info: {image_info}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=image_id,
                            image_info=image_info))
        self.ctx.zone_pg.delete_image(image_id)
        self.ctx.zone_pg.insert_image(image_info)
        logger.info("insert image end, session id: {session_id}, image_id: "
                    "{image_id}, image info:{image_info}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=image_id,
                            image_info=image_info))

    def _update_resource_leasing(self):
        """更新资源计费信息"""
        logger.info("update resource leasing start, session id: {session_id}, "
                    "image id: {image_id}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=self.vm_session.dst_vm_image_id))

        res = self.ctx.iaas.update_resource_leasing(
            self.vm_session.dst_vm_image_id,
            zone=self.vm_session.task.dst_zone_id)
        logger.info("update resource leasing end, session id: {session_id}, "
                    "image id: {image_id}, res: {res}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=self.vm_session.dst_vm_image_id,
                            res=res))

    def _copy_image_to_seed(self):
        """拷贝镜像到seed节点"""
        seed_nodes = SEED_NODES
        image_id = self.vm_session.dst_vm_image_id
        logger.info("copy image to seed node start, session id: {session_id},"
                    " image id: {image_id}, seed nodes: {seed_nodes}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=image_id,
                            seed_nodes=seed_nodes))

        for node in seed_nodes:
            # 创建镜像文件夹
            image_repo_dir = os.path.join(SEED_IMAGE_REPOSITORY_BASE_DIR,
                                          image_id.replace('img-', '')[:2])
            action = "mkdir -p %s" % image_repo_dir
            create_dir_cmd = SSH_CMD_TEMPLATE.format(
                id_rsa=SEED_ID_RSA_PATH,
                option=SSH_CMD_OPTION,
                user=SEED_DEFAULT_USER,
                host=node,
                action=action)
            normal_exec(create_dir_cmd)

            # 拷贝空镜像到文件夹
            dst_path = os.path.join(image_repo_dir, image_id + ".lz4")
            copy_image_cmd = SCP_CMD_TEMPLATE.format(
                id_rsa=SEED_ID_RSA_PATH,
                option=SSH_CMD_OPTION,
                src_path=CREATE_INSTANCE_IMAGE_FILE_PATH,
                user=SEED_DEFAULT_USER,
                host=node,
                dst_path=dst_path)

            logger.info(
                "copy image to seed node ready, session id: {session_id}, "
                "seed: {seed}, copy image cmd: {copy_image_cmd}"
                "".format(session_id=self.vm_session.session_id,
                          seed=node,
                          copy_image_cmd=copy_image_cmd))
            returncode, stdout, stderr = normal_exec(copy_image_cmd)
            if returncode != 0:
                self.vm_session.update_detail_migrate_status(dict(
                    err_code=ErrorCode.CREATE_INSTANCE_ERROR_COPY_IMAGE_TO_SEED_FAILED.value,
                    err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_COPY_IMAGE_TO_SEED_FAILED.value.zh))
                log_msg = "copy image to seed node failed, session id: " \
                          "{session_id}, seed: {seed}, copy image cmd: " \
                          "{copy_image_cmd}, reason: {reason}" \
                          "".format(session_id=self.vm_session.session_id,
                                    seed=node,
                                    copy_image_cmd=copy_image_cmd,
                                    reason=str(stderr))
                logger.error(log_msg)
                raise Exception(log_msg)

        logger.info(
            "copy image to seed node end, session id: {session_id}, image "
            "id: {image_id}"
            .format(session_id=self.vm_session.session_id,
                    image_id=image_id))

    def _delete_image_from_seed(self):
        """从seed节点删除镜像"""
        seed_nodes = SEED_NODES
        image_id = self.vm_session.dst_vm_image_id
        logger.info("delete image from seed node start, session id: "
                    "{session_id}, image id: {image_id}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=image_id))

        for node in seed_nodes:
            # 创建镜像文件夹
            image_path = os.path.join(SEED_IMAGE_REPOSITORY_BASE_DIR,
                                      image_id.replace('img-', '')[:2],
                                      image_id + ".lz4")

            action = 'rm -f %s' % image_path
            delete_image_cmd = SSH_CMD_TEMPLATE.format(
                id_rsa=SEED_ID_RSA_PATH,
                option=SSH_CMD_OPTION,
                user=SEED_DEFAULT_USER,
                host=node,
                action=action)
            logger.info("delete image from seed node ready, session id: "
                        "{session_id}, seed: {seed}, delete image cmd: "
                        "{delete_image_cmd}"
                        "".format(session_id=self.vm_session.session_id,
                                  seed=node,
                                  delete_image_cmd=delete_image_cmd))
            normal_exec(delete_image_cmd)

        logger.info("delete image from seed node end, session id: "
                    "{session_id}, image id: {image_id}"
                    .format(session_id=self.vm_session.session_id,
                            image_id=image_id))

    def _create_dst_vm(self):
        """创建虚拟机"""
        logger.info("create dst vm start, user id: {user_id}, session id: "
                    "{session_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id))

        # 编排vxnet参数
        dst_vm_net = self.vm_session.dst_vm_net[0]
        vxnet_id = dst_vm_net["vxnet_id"]
        if "ip" in dst_vm_net.keys():
            ip = dst_vm_net["ip"]
            vxnet_info = "|".join([vxnet_id, ip]) if ip else vxnet_id
        else:
            vxnet_info = vxnet_id

        try:
            res = self.ctx.iaas.run_instance(
                image_id=self.vm_session.dst_vm_image_id,
                instance_class=self.vm_session.dst_vm_type,
                cpu=self.vm_session.dst_vm_cpu,
                memory=self.vm_session.dst_vm_memory,
                target_user=self.vm_session.task.owner_id,
                os_disk_size=self.vm_session.dst_vm_os_disk["size"],
                instance_name=self.vm_session.dst_vm_name,
                zone=self.vm_session.task.dst_zone_id,
                vxnet_info=vxnet_info,
                hyper_node_id=self.vm_session.indeed_dst_node_id)

            wait_job_successful(res["job_id"],
                                CREATE_INSTANCE_RUN_INSTANCE_TIMEOUT)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_RUN_INSTANCE_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_RUN_INSTANCE_FAILED.value.zh))

            log_msg = "create dst vm failed, user id: {user_id}, session id: " \
                      "{session_id}, error reason: {error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        instance_id = res['instances'][0]
        self.vm_session.dst_vm_os_disk["volume_id"] = instance_id
        self.vm_session.dst_vm_os_disk["volume_name"] = ".".join(
            [instance_id, "img"])
        self.vm_session.dst_vm_os_disk["pool"] = "vol"
        # from constants.template import GET_POOL_BY_VOLUME_CMD_TEMPLATE
        # pool = normal_exec(GET_POOL_BY_VOLUME_CMD_TEMPLATE(volume_id=instance_id))
        # self.vm_session.dst_vm_os_disk["pool"] = pool

        instance_info = self.ctx.iaas.describe_instance(
            instance_id=instance_id,
            zone=self.vm_session.task.dst_zone_id)
        host_machine = instance_info["host_machine"]
        if instance_info["host_machine"] != self.vm_session.indeed_dst_node_id:
            logger.error(
                "run node is not valid, host machine: {host_machine}, "
                "indeed dst node id: {indeed_dst_node_id}"
                "".format(host_machine=host_machine,
                          indeed_dst_node_id=self.vm_session.indeed_dst_node_id))
            raise Exception

        self.vm_session.info["dst_vm_create_time"] = get_current_time()
        self.vm_session.info["dst_vm_id"] = instance_id
        self.vm_session.update_to_mem_and_pg(self.vm_session.info)
        logger.info("create dst vm end, user id: {user_id}, session id: "
                    "{session_id}, dst vm id: {dst_vm_id}"
                    .format(session_id=self.vm_session.session_id,
                            dst_vm_id=instance_id,
                            user_id=self.vm_session.user_id))

    def _describe_instance(self):
        """查询虚拟机"""
        instance_id = self.vm_session.dst_vm_id
        zone = self.vm_session.task.dst_zone_id
        return self.ctx.iaas.describe_instance(instance_id, zone=zone)

    def _start_dst_vm(self):
        """启动目标虚拟机"""
        logger.info("start dst vm start, user id: {user_id}, session id: "
                    "{session_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id))

        instance_id = self.vm_session.dst_vm_id
        zone = self.vm_session.task.dst_zone_id
        status = self.ctx.iaas.describe_instance(instance_id, zone=zone)[
            "status"]

        # 如果本身为运行状态，则直接返回
        if status == INST_STATUS_RUN:
            logger.info("instance now is already running, do not need start "
                        "instance, session id: {session_id}, dst vm id: "
                        "{dst_vm_id}"
                        .format(session_id=self.vm_session.session_id,
                                dst_vm_id=instance_id))
            return

        # 如果本身为启动中状态，则阻塞等待启动成功
        if status == INST_TRAN_STATUS_STARTING:
            max_retry_times = 60
            already_retry_times = 0
            while True:
                time.sleep(5)
                status = \
                self.ctx.iaas.describe_instance(instance_id, zone=zone)[
                    "status"]
                if status == INST_STATUS_RUN:
                    # 虚拟机运行状态，直接返回
                    return
                if status == INST_STATUS_STOP:
                    # 因为不可预知因素导致虚拟机被关机，直接走重新开机流程
                    break
                already_retry_times += 1
                if already_retry_times >= max_retry_times:
                    self.vm_session.update_detail_migrate_status(dict(
                        err_code=ErrorCode.CREATE_INSTANCE_ERROR_START_INSTANCE_FAILED.value,
                        err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_START_INSTANCE_FAILED.value.zh))

                    log_msg = "start dst vm timeout, session id: " \
                              "{session_id}, dst vm id: {dst_vm_id}, already " \
                              "retry times: {already_retry_times}" \
                              "".format(session_id=self.vm_session.session_id,
                                        dst_vm_id=self.vm_session.dst_vm_id,
                                        already_retry_times=already_retry_times)
                    logger.error(log_msg)
                    raise Exception(log_msg)

        # 执行开机
        try:
            res = self.ctx.iaas.start_instance(instance_id, zone=zone)
            assert res["job_id"]
            wait_job_successful(res["job_id"],
                                CREATE_INSTANCE_START_INSTANCE_TIMEOUT)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_START_INSTANCE_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_START_INSTANCE_FAILED.value.zh))

            log_msg = "start dst vm failed, user id: {user_id}, session id: " \
                      "{session_id}, dst vm id: {dst_vm_id}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                dst_vm_id=instance_id,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        logger.info("start dst vm end, user id: {user_id}, session id: "
                    "{session_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id))

    def _restart_dst_vm(self):
        """重启虚拟机"""
        instance_id = self.vm_session.dst_vm_id
        logger.info("restart dst vm start, user id: {user_id}, session id: "
                    "{session_id}, dst vm id: {dst_vm_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id,
                              dst_vm_id=instance_id))
        zone = self.vm_session.task.dst_zone_id
        status = self.ctx.iaas.describe_instance(instance_id, zone=zone)[
            "status"]

        # 如果本身为已经关闭的状态，则直接开机
        if status == INST_STATUS_STOP:
            logger.info("instance now is already stopped, can not restart "
                        "instance, session id: {session_id}, instance id: "
                        "{instance_id}"
                        .format(session_id=self.vm_session.session_id,
                                instance_id=instance_id))
            self._start_dst_vm()

        # 执行重启
        try:
            res = self.ctx.iaas.restart_instance(instance_id, zone=zone)
            assert res["job_id"]
            wait_job_successful(res["job_id"],
                                CREATE_INSTANCE_RESTART_INSTANCE_TIMEOUT)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_RESTART_INSTANCE_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_RESTART_INSTANCE_FAILED.value.zh))

            log_msg = "restart dst vm failed, user id: {user_id}, session id: " \
                      "{session_id}, dst vm id: {dst_vm_id}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                dst_vm_id=instance_id,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        logger.info("restart dst vm end, user id: {user_id}, session id: "
                    "{session_id}, dst vm id: {dst_vm_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id,
                              dst_vm_id=instance_id))

    def _stop_dst_vm(self):
        """关闭虚拟机"""
        instance_id = self.vm_session.dst_vm_id
        logger.info("stop dst vm start, user id: {user_id}, session id: "
                    "{session_id}, dst vm id: {dst_vm_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id,
                              dst_vm_id=instance_id))

        # 如果本身为关机状态，则直接返回
        zone = self.vm_session.task.dst_zone_id
        status = self.ctx.iaas.describe_instance(instance_id, zone=zone)[
            "status"]
        if status == INST_STATUS_STOP:
            logger.info("dst vm now is already stopped, do not need stop "
                        "instance, session id: {session_id}, dst vm id: "
                        "{dst_vm_id}"
                        .format(session_id=self.vm_session.session_id,
                                dst_vm_id=instance_id))
            return

        # 执行关机
        try:
            res = self.ctx.iaas.stop_instance(instance_id, 1, zone=zone)
            assert res["job_id"]
            wait_job_successful(res["job_id"],
                                CREATE_INSTANCE_STOP_INSTANCE_TIMEOUT)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_STOP_INSTANCE_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_STOP_INSTANCE_FAILED.value.zh))

            log_msg = "stop dst vm failed, user id: {user_id}, session id: " \
                      "{session_id}, dst vm id: {dst_vm_id}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                dst_vm_id=instance_id,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        logger.info("stop dst vm end, user id: {user_id}, session id: "
                    "{session_id}, dst vm id: {dst_vm_id}"
                    "".format(session_id=self.vm_session.session_id,
                              user_id=self.vm_session.user_id,
                              dst_vm_id=instance_id))

    def _update_dst_vm_image_status(self):
        """更新镜像状态"""
        columns = dict(status=ImageStatus.DEPRECATED.value)
        image_id = self.vm_session.dst_vm_image_id
        try:
            self.ctx.zone_pg.update_image(image_id, columns=columns)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_UPDATE_IMAGE_STATUS_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_UPDATE_IMAGE_STATUS_FAILED.value.zh))
            log_msg = "update image status failed, user id: {user_id}, session " \
                      "id: {session_id}, image id: {image_id}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                image_id=image_id,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

    def _create_dst_vm_disks(self):
        """创建硬盘
        Note:只有数据盘需要创建
        """
        logger.info(
            "create dst vm disks start, session id: {session_id}, dst vm "
            "disk: {dst_vm_disk}"
            .format(session_id=self.vm_session.session_id,
                    dst_vm_disk=self.vm_session.dst_vm_disk))

        dst_vm_data_disk = self.vm_session.dst_vm_data_disk
        if not dst_vm_data_disk:
            logger.info(
                "there is not data disk in dst vm, session id: {session_id}, "
                "dst vm id: {dst_vm_id}"
                "".format(session_id=self.vm_session.session_id,
                          dst_vm_id=self.vm_session.dst_vm_id))
            return

        try:
            for disk_info in dst_vm_data_disk:
                res = self.ctx.iaas.create_volume(
                    volume_name=disk_info["name"],
                    volume_type=disk_info["volume_type"],
                    size=disk_info["size"],
                    target_user=self.vm_session.task.owner_id,
                    hyper_node_id=self.vm_session.indeed_dst_node_id,
                    zone=self.vm_session.task.dst_zone_id)
                assert res["job_id"]
                wait_job_successful(res["job_id"],
                                    CREATE_INSTANCE_CREATE_VOLUMES_TIMEOUT)
                volume_id = res['volumes'][0]

                disk_info["volume_id"] = volume_id
                disk_info["volume_name"] = ".".join([volume_id, "img"])

                if disk_info["volume_type"] in SANCVolumeType.list_type():
                    disk_info["pool"] = "vol"
                    # from constants.template import GET_POOL_BY_VOLUME_CMD_TEMPLATE
                    # pool = normal_exec(GET_POOL_BY_VOLUME_CMD_TEMPLATE(volume_id=volume_id))
                    # disk_info["pool"] = pool

            # 更新配置
            self.vm_session.update_to_pg(
                dict(dst_vm_disk=self.vm_session.dst_vm_disk))
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_CREATE_VOLUMES_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_CREATE_VOLUMES_FAILED.value.zh))
            log_msg = "create dst vm disks failed, user id: {user_id}, session id: " \
                      "{session_id}, dst vm disk: {dst_vm_disk}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                dst_vm_disk=self.vm_session.dst_vm_disk,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        logger.info(
            "create dst vm disks end, session id: {session_id}, dst vm disk"
            ": {dst_vm_disk}"
            .format(session_id=self.vm_session.session_id,
                    dst_vm_disk=self.vm_session.dst_vm_disk))

    def _attach_dst_vm_disks(self):
        """加载硬盘
        Note:只有数据盘需要加载
        """
        dst_vm_data_disk = self.vm_session.dst_vm_data_disk
        logger.info(
            "attach dst vm disks start, session id: {session_id}, dst vm"
            " data disk: {dst_vm_data_disk}"
            .format(session_id=self.vm_session.session_id,
                    dst_vm_data_disk=dst_vm_data_disk))

        if not dst_vm_data_disk:
            logger.info(
                "there is not data disk in dst vm, session id: {session_id}, "
                "dst vm id: {dst_vm_id}"
                "".format(session_id=self.vm_session.session_id,
                          dst_vm_id=self.vm_session.dst_vm_id))
            return

        try:
            volume_id_list = [disk_info["volume_id"]
                              for disk_info in dst_vm_data_disk]
            res = self.ctx.iaas.attach_volumes(
                instance_id=self.vm_session.dst_vm_id,
                volume_id_list=volume_id_list,
                zone=self.vm_session.task.dst_zone_id)
            assert res["job_id"]
            wait_job_successful(res["job_id"],
                                CREATE_INSTANCE_ATTACH_VOLUMES_TIMEOUT)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_ATTACH_VOLUMES_FAILED.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_ATTACH_VOLUMES_FAILED.value.zh))

            log_msg = "attach dst vm disks failed, user id: {user_id}, session id: " \
                      "{session_id}, dst vm data disk: {dst_vm_data_disk}, " \
                      "error reason: {error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                dst_vm_data_disk=dst_vm_data_disk,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        logger.info(
            "attach dst vm disks end, session id: {session_id}, dst vm id:"
            " {dst_vm_id}, dst vm data disk: {dst_vm_data_disk}, "
            "volume id list: {volume_id_list}"
            .format(session_id=self.vm_session.session_id,
                    dst_vm_id=self.vm_session.dst_vm_id,
                    dst_vm_data_disk=dst_vm_data_disk,
                    volume_id_list=volume_id_list))

    def _cover_image_by_move(self, disk_info):
        """通过剪切的方式覆盖镜像"""
        start_time = datetime.datetime.now()
        qcow2_path = disk_info["qcow2_path"]
        qcow2_size = disk_info["qcow2_size"]
        volume_id = disk_info["volume_id"]
        volume_name = disk_info["volume_name"]

        logger.info(
            "cover image by move start, session id:"
            " {session_id}, dst vm id: {dst_vm_id}, disk name: "
            "{disk_name}, qcow2 path: {qcow2_path}, qcow2 size: "
            "{qcow2_size}MB, is os disk: {is_os_disk}, volume type"
            ": {volume_type}, volume id: {volume_id}"
            "".format(session_id=self.vm_session.session_id,
                      dst_vm_id=self.vm_session.dst_vm_id,
                      disk_name=disk_info["name"],
                      qcow2_path=qcow2_path,
                      qcow2_size=qcow2_size,
                      is_os_disk=disk_info["is_os_disk"],
                      volume_type=disk_info["volume_type"],
                      volume_id=volume_id))

        if os.path.exists(os.path.join(HYPER_IMAGE_BASE_DIR, volume_id)):
            volume_dir = os.path.join(HYPER_IMAGE_BASE_DIR, volume_id)
        else:
            volume_dir = HYPER_IMAGE_BASE_DIR
        volume_path = os.path.join(volume_dir, volume_name)
        if not os.path.exists(volume_path):
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.CREATE_INSTANCE_ERROR_VOLUME_NOT_EXISTS.value,
                err_msg=ErrorMsg.CREATE_INSTANCE_ERROR_VOLUME_NOT_EXISTS.value.zh))
            log_msg = "volume path not exists, session id: {session_id}, " \
                      "volume path: {volume_path}" \
                      "".format(session_id=self.vm_session.session_id,
                                volume_path=volume_path)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 覆盖数据
        logger.info("cover image by move ready, session id:"
                    " {session_id}, disk name: {disk_name}, qcow2 path: "
                    "{qcow2_path}, volume path: {volume_path}"
                    "".format(session_id=self.vm_session.session_id,
                              disk_name=disk_info["name"],
                              qcow2_path=qcow2_path,
                              volume_path=volume_path))
        shutil.move(qcow2_path, volume_path)

        # 统计数据
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        time_strftime = str(datetime.timedelta(seconds=total_seconds))
        logger.info(
            "cover image by move successfully, session id:"
            " {session_id}, dst vm id: {dst_vm_id}, disk name: "
            "{disk_name}, qcow2 path: {qcow2_path}, qcow2 size: "
            "{qcow2_size}MB, is os disk: {is_os_disk}, volume type"
            ": {volume_type}, volume id: {volume_id}, volume path: "
            "{volume_path}, cost time: {cost_time}, cover speed: "
            "{cover_speed}MB/s"
            "".format(session_id=self.vm_session.session_id,
                      dst_vm_id=self.vm_session.dst_vm_id,
                      disk_name=disk_info["name"],
                      qcow2_path=qcow2_path,
                      qcow2_size=qcow2_size,
                      is_os_disk=disk_info["is_os_disk"],
                      volume_type=disk_info["volume_type"],
                      volume_id=volume_id,
                      volume_path=volume_path,
                      cost_time=time_strftime,
                      cover_speed=round(qcow2_size / total_seconds, 2)))

    def _cover_image_by_dd(self, disk_info):
        """通过dd的方式覆盖镜像"""
        start_time = datetime.datetime.now()
        qcow2_path = disk_info["qcow2_path"]
        qcow2_size = disk_info["qcow2_size"]
        volume_id = disk_info["volume_id"]

        logger.info(
            "cover image by dd start, session id:"
            " {session_id}, dst vm id: {dst_vm_id}, disk name: "
            "{disk_name}, qcow2 path: {qcow2_path}, qcow2 size: "
            "{qcow2_size}MB, is os disk: {is_os_disk}, volume type"
            ": {volume_type}, volume id: {volume_id}"
            "".format(session_id=self.vm_session.session_id,
                      dst_vm_id=self.vm_session.dst_vm_id,
                      disk_name=disk_info["name"],
                      qcow2_path=qcow2_path,
                      qcow2_size=qcow2_size,
                      is_os_disk=disk_info["is_os_disk"],
                      volume_type=disk_info["volume_type"],
                      volume_id=volume_id))

        assert self.vm_session.indeed_dst_node_id == self.ctx.local_node.node_id
        # 将qcow2镜像文件映射为网络块设备
        with map_nbd_device_context(qcow2_path) as img_info:
            # 将NeonSAN磁盘映射为qbd网络块设备
            with map_qbd_device_context(volume_id) as qbd_dev_path:
                # 拷贝nbd设备（背后就是源qcow2镜像）数据到qbd设备（背后就是neonsan硬盘）
                cover_cmd = "dd if={src_dev} bs=4k of={dst_dev}".format(
                    src_dev=img_info["dev_path"], dst_dev=qbd_dev_path)
                logger.info(
                    "cover image by dd ready, session id: {session_id}, disk"
                    " name: {disk_name}, qcow2 path: {qcow2_path}, cover "
                    "cmd: {cover_cmd}"
                    "".format(session_id=self.vm_session.session_id,
                              disk_name=disk_info["name"],
                              qcow2_path=qcow2_path,
                              cover_cmd=cover_cmd))
                returncode, stdout, stderr = normal_exec(cover_cmd,
                                                         COVER_IMAGE_TIMEOUT)
                if returncode != 0:
                    self.vm_session.update_detail_migrate_status(dict(
                        err_code=ErrorCode.COVER_IMAGE_ERROR_COMMON.value,
                        err_msg=ErrorMsg.COVER_IMAGE_ERROR_COMMON.value.zh))
                    log_msg = "cover image by dd failed, session id: {session_id}, " \
                              "qcow2 path: {qcow2_path}, stderr: {stderr}, " \
                              "stdout: {stdout}" \
                              "".format(session_id=self.vm_session.session_id,
                                        qcow2_path=qcow2_path,
                                        stderr=stderr,
                                        stdout=stdout)
                    logger.error(log_msg)
                    raise Exception(log_msg)

        # 统计数据
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        time_strftime = str(datetime.timedelta(seconds=total_seconds))
        logger.info(
            "cover image by dd successfully, session id:"
            " {session_id}, dst vm id: {dst_vm_id}, disk name: "
            "{disk_name}, qcow2 path: {qcow2_path}, qcow2 size: "
            "{qcow2_size}MB, is os disk: {is_os_disk}, volume type"
            ": {volume_type}, volume id: {volume_id}, cost time: "
            "{cost_time}, cover speed: {cover_speed}MB/s"
            "".format(session_id=self.vm_session.session_id,
                      dst_vm_id=self.vm_session.dst_vm_id,
                      disk_name=disk_info["name"],
                      qcow2_path=qcow2_path,
                      qcow2_size=qcow2_size,
                      is_os_disk=disk_info["is_os_disk"],
                      volume_type=disk_info["volume_type"],
                      volume_id=volume_id,
                      cost_time=time_strftime,
                      cover_speed=round(qcow2_size / total_seconds, 2)))

    def identify_src_vm_os_disk(self, qcow2_path):
        is_os_disk = self._identify_src_vm_os_disk(qcow2_path)
        if is_os_disk is not None:
            return is_os_disk

        # 走到这里，意味着当前的方法均无法判断
        self.vm_session.update_detail_migrate_status(dict(
            err_code=ErrorCode.CONVERT_IMAGE_ERROR_IDENTIFY_OS_DISK_FAILED.value,
            err_msg=ErrorMsg.CONVERT_IMAGE_ERROR_IDENTIFY_OS_DISK_FAILED.value.zh))
        log_msg = "identify os disk failed, image file: " \
                  "{image_file}, error reason: {error_reason}" \
                  "".format(image_file=qcow2_path,
                            error_reason=ErrorMsg.CONVERT_IMAGE_ERROR_IDENTIFY_OS_DISK_FAILED.value.en)
        logger.error(log_msg)
        raise Exception(log_msg)

    def _identify_src_vm_os_disk(self, qcow2_path):
        """识别镜像文件关联的硬盘是否为系统盘"""

        if self.vm_session.dst_vm_disk_num == 1:
            return True

        with map_nbd_device_context(qcow2_path) as img_info:
            if not img_info["has_partition"]:
                return False

            if self.vm_session.dst_vm_os_type == InstanceOSType.WINDOWS.value:
                return self._identify_windows_os_disk_by_boot(img_info)

            if self.vm_session.dst_vm_os_type in InstanceOSType.list_linux_type():
                return self._identify_linux_os_disk_by_fdisk(img_info)

    @staticmethod
    def _identify_windows_os_disk_by_boot(img_info):
        """windows操作系统依据boot文件判断是否为系统盘"""
        partition_info = img_info["partition_info"]

        tag_file_list = ["bootx64.efi", "boot.ini", "AUTOEXEC.BAT"]
        for indeed_dev_path, partition_mnt_dir in partition_info.items():
            os.makedirs(partition_mnt_dir) if not os.path.isdir(
                partition_mnt_dir) else None

            # 挂载，读取内容并判断是否为系统盘
            with mount_nbd_device_context(partition_mnt_dir,
                                          indeed_dev_path) as is_success:
                if not is_success:
                    continue

                if "Windows" in os.listdir(partition_mnt_dir):
                    return True

                if "Boot" in os.listdir(partition_mnt_dir):
                    return True

                if "Program Files" in os.listdir(partition_mnt_dir):
                    return True

                if find_file(partition_mnt_dir, tag_file_list, False):
                    return True
        else:
            return False

    def _identify_linux_os_disk_by_fdisk(self, img_info):
        """linux操作系统依据fdisk命令判断是否为系统盘"""
        dev_path = img_info["dev_path"]
        cmd = "fdisk -l %s | grep %s | grep -v 'Linux LVM' | grep -E " \
              "'Linux|W95 FAT32' | awk -F ' ' '{print $2}'" \
              % (dev_path, dev_path)
        returncode, stdout, stderr = normal_exec(cmd)
        if returncode == 0:
            if stdout:
                logger.info("get suitable boot info, session id: {session_id}"
                            ", boot info: {boot_info}"
                            .format(session_id=self.vm_session.session_id,
                                    boot_info=stdout))
                if "*" in stdout.split("\n"):
                    return True

        partition_info = img_info["partition_info"]
        for indeed_dev_path, partition_mnt_dir in partition_info.items():
            os.makedirs(partition_mnt_dir) if not os.path.isdir(
                partition_mnt_dir) else None

            # 挂载，读取内容并判断是否为系统盘
            with mount_nbd_device_context(partition_mnt_dir,
                                          indeed_dev_path) as is_success:
                if not is_success:
                    continue

                if "boot" in os.listdir(partition_mnt_dir):
                    return True

                if "root" in os.listdir(partition_mnt_dir):
                    return True

                if "EFI" in os.listdir(partition_mnt_dir):
                    return True

                if "grub" in os.listdir(partition_mnt_dir):
                    return True
        else:
            return False

    def _patch_drive(self):
        """处理驱动问题"""
        pass

    def _upload_proxy(self):
        """上传代理"""
        pass


class ExportImageMigration(BaseMigration):
    """导出镜像模式对应的迁移器"""
    migrate_pattern = MigratePattern.EXPORT_IMAGE.value

    def __init__(self, vm_session):
        super(ExportImageMigration, self).__init__(vm_session)
        self.ova_path = ""

    def export_image(self):
        """导出镜像"""
        logger.info("export image start, session id: {session_id}, src vm "
                    "name: {src_vm_name}"
                    .format(session_id=self.vm_session.session_id,
                            src_vm_name=self.vm_session.src_vm_name))
        # 更新详细的迁移状态信息
        start_status = RunningDetailMigrateStatus.START_EXPORT_IMAGE_DETAIL_STATUS.value
        start_status["step"]["start_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(start_status)

        """
        命令格式
        {ovf_tool_path} {cmd_params} 
        '{cmd_prefix}{username}:{password}@{ip}:{port}/{datacenter}/{vm_dir}/{vm_folder}/{src_vm_name}' 
        {dst_dir}/{dst_vm_name}.{dst_image_format}
        """

        # 目前写死， 后续再酌情优化
        disk_mode_param = "--diskMode=thin"
        advanced_params = " ".join([disk_mode_param])

        src_platform = self.vm_session.task.src_platform
        export_image_cmd = EXPORT_IMAGE_CMD_TEMPLATE.format(
            ovf_tool_path=HYPER_VMWARE_OVF_TOOL_PATH,
            common_params=EXPORT_IMAGE_DEFAULT_PARAMS,
            advanced_params=advanced_params,
            cmd_prefix=EXPORT_IMAGE_CMD_VI_PREFIX,
            username=src_platform.user,
            password=aes_decode(src_platform.password),
            ip=src_platform.ip,
            port=str(src_platform.port),
            datacenter=self.vm_session.task.src_datacenter_name,
            vm_dir="vm",
            vm_folder=self.vm_session.src_vm_folder,
            src_vm_name=self.vm_session.src_vm_name,
            dst_dir=self.vm_session.export_dir,
            dst_vm_name=self.vm_session.dst_vm_name,
            dst_image_format=EXPORT_IMAGE_DST_FORMAT_OVA)
        logger.info("export image ready, session id: {session_id}, src vm "
                    "name: {src_vm_name}, export image cmd: {cmd}"
                    .format(session_id=self.vm_session.session_id,
                            src_vm_name=self.vm_session.src_vm_name,
                            cmd=export_image_cmd))
        start_time = datetime.datetime.now()

        # 执行导出镜像命令
        execute_times = 0
        while True:
            execute_times += 1
            logger.info(
                "export image, execute times: {execute_times} times, max "
                "retry times: {max_retry_times} times, session id: "
                "{session_id}"
                .format(execute_times=execute_times,
                        max_retry_times=EXPORT_IMAGE_MAX_RETRY_TIMES,
                        session_id=self.vm_session.session_id))
            returncode, stdout, stderr = normal_exec(export_image_cmd,
                                                     EXPORT_IMAGE_TIMEOUT)
            if returncode == 0:
                break

            if execute_times >= EXPORT_IMAGE_MAX_RETRY_TIMES:
                self.vm_session.update_detail_migrate_status(dict(
                    err_code=ErrorCode.EXPORT_IMAGE_ERROR_COMMON.value,
                    err_msg=ErrorMsg.EXPORT_IMAGE_ERROR_COMMON.value.zh))

                log_msg = "export image failed, retry times has out of limit, " \
                          "session id: {session_id}, export image cmd: {cmd}, " \
                          "error reason: {error_reason}" \
                          "".format(session_id=self.vm_session.session_id,
                                    cmd=export_image_cmd,
                                    error_reason=stderr)
                logger.error(log_msg)
                raise Exception(log_msg)
            time.sleep(10)

        # 检查OVA文件是否成功下载
        ova_name = ".".join(
            [self.vm_session.dst_vm_name, EXPORT_IMAGE_DST_FORMAT_OVA])
        self.ova_path = os.path.join(self.vm_session.export_dir, ova_name)
        if not os.path.isfile(self.ova_path):
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.EXPORT_IMAGE_ERROR_OVA_NOT_EXISTS.value,
                err_msg=ErrorMsg.EXPORT_IMAGE_ERROR_OVA_NOT_EXISTS.value.zh))

            log_msg = "export image failed, can not find ova file, session " \
                      "id: {session_id}, ova path: {ova_path}" \
                      "".format(session_id=self.vm_session.session_id,
                                ova_path=self.ova_path)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 更新详细的迁移状态信息
        end_status = RunningDetailMigrateStatus.END_EXPORT_IMAGE_DETAIL_STATUS.value
        end_status["step"]["end_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(end_status)

        # 统计数据
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        time_strftime = str(datetime.timedelta(seconds=total_seconds))
        ova_size = get_file_size(self.ova_path)
        export_speed = ova_size / total_seconds  # 单位：MB/s
        logger.info("export image end, session id: {session_id}, cost time: "
                    "{cost_time}, execute times: {execute_times} times, "
                    "ova size: {ova_size}MB, export speed: {export_speed}MB/s"
                    ", ova path: {ova_path}"
                    .format(session_id=self.vm_session.session_id,
                            ova_path=self.ova_path,
                            ova_size=ova_size,
                            cost_time=time_strftime,
                            execute_times=execute_times,
                            export_speed=export_speed))

    def _uncompress_image(self):
        """解压镜像"""
        logger.info("uncompress image start, session id: {session_id}, "
                    "ova path: {ova_path}".
                    format(session_id=self.vm_session.session_id,
                           ova_path=self.ova_path))
        vmdk_dir = os.path.join(self.vm_session.export_dir,
                                self.vm_session.dst_vm_name)
        shutil.rmtree(vmdk_dir) if os.path.isdir(vmdk_dir) else None
        os.mkdir(vmdk_dir)
        start_time = datetime.datetime.now()
        try:
            tar = tarfile.open(self.ova_path)
            for single_file in tar.getnames():
                if single_file.endswith("ovf"):
                    tar.extract(single_file, self.vm_session.export_dir)
                    self.ovf_path = os.path.join(self.vm_session.export_dir,
                                                 single_file)
                elif single_file.endswith("vmdk"):
                    tar.extract(single_file, vmdk_dir)
                    self.vmdk_path_list.append(
                        os.path.join(vmdk_dir, single_file))
                elif single_file.endswith("mf"):
                    tar.extract(single_file, self.vm_session.export_dir)
                    self.mf_path = os.path.join(self.vm_session.export_dir,
                                                single_file)
                else:
                    continue
            tar.close()
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.DEAL_IMAGE_ERROR_UNCOMPRESS_IMAGE_FAILED.value,
                err_msg=ErrorMsg.DEAL_IMAGE_ERROR_UNCOMPRESS_IMAGE_FAILED.value.zh))

            log_msg = "uncompress image failed, user id: {user_id}, session id: " \
                      "{session_id}, ova path: {ova_path}, error reason: " \
                      "{error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                user_id=self.vm_session.user_id,
                                ova_path=self.ova_path,
                                error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

        # 记录结束时间并统计
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        time_strftime = str(datetime.timedelta(seconds=total_seconds))
        ova_size = get_file_size(self.ova_path)
        uncompress_speed = ova_size / total_seconds  # 单位: MB/s

        logger.info("uncompress image end, session id: {session_id}, cost time"
                    ": {cost_time}, ova_size: {ova_size}MB, uncompress speed: "
                    "{uncompress_speed}MB/s, ova path: {ova_path}, "
                    "vmdk path list: {vmdk_path_list}, ovf path: {ovf_path}"
                    .format(cost_time=time_strftime,
                            session_id=self.vm_session.session_id,
                            vmdk_path_list=self.vmdk_path_list,
                            ovf_path=self.ovf_path,
                            ova_size=ova_size,
                            ova_path=self.ova_path,
                            uncompress_speed=uncompress_speed))

    def check_image(self):
        """检查镜像"""
        return self._check_image()

    def _check_image(self):
        """检查镜像
        # 1.完整性检查
        # 2.检查文件的SHA256值
        """

        logger.info("check image start, session id: {session_id}, ova path: "
                    "{ova_path}, mf path: {mf_path}"
                    .format(session_id=self.vm_session.session_id,
                            ova_path=self.ova_path,
                            mf_path=self.mf_path))
        if not self.mf_path:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.DEAL_IMAGE_ERROR_MF_NOT_EXISTS.value,
                err_msg=ErrorMsg.DEAL_IMAGE_ERROR_MF_NOT_EXISTS.value.zh))

            log_msg = "mf file is not exists, session id: %s" % \
                      self.vm_session.session_id
            logger.error(log_msg)
            raise Exception(log_msg)

        sha256_format = "SHA256({fname})"
        mf_data = {}
        mf_content = read_file(self.mf_path)
        items = mf_content.split("\n")
        for line in items:
            if line:
                key, value = line.split("=")
                if key not in mf_data:
                    mf_data[key] = value.strip()
        logger.info("mf data: {mf_data}, session id: {session_id}"
                    .format(mf_data=mf_data,
                            session_id=self.vm_session.session_id))

        # 检查ovf文件
        ovf_name = os.path.basename(self.ovf_path)
        ovf_key = sha256_format.format(fname=ovf_name)
        ovf_content = read_file(self.ovf_path)
        ovf_sha256 = sha256_tool(ovf_content)
        if mf_data.get(ovf_key) != ovf_sha256:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.DEAL_IMAGE_ERROR_OVF_NOT_MATCH.value,
                err_msg=ErrorMsg.DEAL_IMAGE_ERROR_OVF_NOT_MATCH.value.zh))

            log_msg = "ovf file {file_name} md5 is not match, mf md5: {mf_md5}" \
                      ", ovf md5: {ovf_md5}" \
                      "".format(file_name=ovf_name,
                                mf_md5=mf_data.get(ovf_key),
                                ovf_md5=ovf_sha256)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 检查vmdk文件
        for vmdk_path in self.vmdk_path_list:
            vmdk_name = os.path.basename(vmdk_path)
            vmdk_key = sha256_format.format(fname=vmdk_name)
            vmdk_content = read_file(vmdk_path)
            vmdk_sha256 = sha256_tool(vmdk_content)
            if mf_data.get(vmdk_key) != vmdk_sha256:
                self.vm_session.update_detail_migrate_status(dict(
                    err_code=ErrorCode.DEAL_IMAGE_ERROR_VMDK_NOT_MATCH.value,
                    err_msg=ErrorMsg.DEAL_IMAGE_ERROR_VMDK_NOT_MATCH.value.zh))

                log_msg = "vmdk file {file_name} md5 is not match, " \
                          "mf md5: {mf_md5}, vmdk md5: {vmdk_md5}" \
                          "".format(file_name=ovf_name,
                                    mf_md5=mf_data.get(ovf_key),
                                    vmdk_md5=vmdk_sha256)
                logger.error(log_msg)
                raise Exception(log_msg)

        logger.info("check image end, session id: {session_id}, "
                    "ova path: {ova_path}, mf path: {mf_path}".
                    format(session_id=self.vm_session.session_id,
                           ova_path=self.ova_path,
                           mf_path=self.mf_path))


class UploadImageMigration(BaseMigration):
    """上传镜像模式对应的迁移器"""
    migrate_pattern = MigratePattern.UPLOAD_IMAGE.value

    def __init__(self, vm_session):
        super(UploadImageMigration, self).__init__(vm_session)

    def upload_image(self):
        """上传镜像"""
        logger.info("upload image start, session id: {session_id}"
                    .format(session_id=self.vm_session.session_id))
        # 更新详细的迁移状态信息
        start_status = RunningDetailMigrateStatus.START_UPLOAD_IMAGE_DETAIL_STATUS.value
        start_status["step"]["start_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(start_status)

        start_time = datetime.datetime.now()
        try:
            src_vm_nfs_path = self.vm_session.src_vm_nfs_path
            dst_vm_name = self.vm_session.dst_vm_name

            # 初始化vmdk目录
            vmdk_dir = os.path.join(self.vm_session.upload_dir, dst_vm_name)
            shutil.rmtree(vmdk_dir) if os.path.isdir(vmdk_dir) else None
            os.mkdir(vmdk_dir)

            total_size = 0
            nfs = NFSInterface(src_vm_nfs_path)
            for single_file in nfs.listdirs(""):
                file_path = os.path.join(src_vm_nfs_path, single_file)
                if single_file.endswith('ovf'):
                    self.ovf_path = os.path.join(self.vm_session.upload_dir,
                                                 single_file)
                    copy_nfs_file(file_path, self.ovf_path)
                    total_size += os.path.getsize(self.ovf_path)
                elif single_file.endswith('vmdk'):
                    vmdk_path = os.path.join(vmdk_dir, single_file)
                    copy_nfs_file(file_path, vmdk_path,
                                  timeout=UPLOAD_IMAGE_TIMEOUT)
                    total_size += os.path.getsize(vmdk_path)
                    self.vmdk_path_list.append(vmdk_path)
        except Exception as e:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.UPLOAD_IMAGE_ERROR_COMMON.value,
                err_msg=ErrorMsg.UPLOAD_IMAGE_ERROR_COMMON.value.zh))

            log_msg = "upload image failed, session id: {session_id}, error " \
                      "reason: {error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                error_reason=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)

        # 更新详细的迁移状态信息
        end_status = RunningDetailMigrateStatus.END_UPLOAD_IMAGE_DETAIL_STATUS.value
        end_status["step"]["end_time"] = now_local_format()
        self.vm_session.update_detail_migrate_status(end_status)

        # 汇总数据
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        time_strftime = str(datetime.timedelta(seconds=total_seconds))
        total_size = round(total_size / float(1024 * 1024), 2)
        upload_speed = total_size / total_seconds  # 单位：MB/s
        logger.info("upload image end, session id: {session_id}, cost_time: "
                    "{cost_time}, total_size: {total_size}MB, upload speed: "
                    "{upload_speed}MB/s"
                    .format(cost_time=time_strftime,
                            total_size=total_size,
                            upload_speed=upload_speed,
                            session_id=self.vm_session.session_id))
