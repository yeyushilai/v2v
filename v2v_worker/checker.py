# -*- coding: utf-8 -*-

"""功能：迁移的检查器"""

import os.path

from log.logger import logger

from api.constants import (
    BLOCK_BUS_TYPE_VD,
    BLOCK_BUS_TYPE_HD,
    BLOCK_BUS_TYPE_SD,

    SUPPORTED_NIC_TYPES,
)

from constants.common import (
    MigratePattern,
    MigrateStatus
)
from constants.iaas import (
    InstanceBootLoaderType,
    InstanceOSType,
    INSTANCE_MEMORY_TYPE,
    INSTANCE_CPU_TYPE
)
from constants.vmware_vsphere import SrcVmStatus
from constants.error import ErrorMsg, ErrorCode
from resource_control.nas.interface import NFSInterface
from uutils.xml_convertor import xml_data_to_json_data


class BaseChecker(object):
    def __init__(self, vm_session):
        self.vm_session = vm_session

    def check(self):
        """检查
        检查通过，返回True，检查不通过，修改状态为失败，返回False
        """
        try:
            self._check()
        except Exception as e:
            # 更新状态
            detail_status = dict(status=MigrateStatus.FAILED.value)
            if not self.vm_session.err_msg:
                detail_status["err_msg"] = ErrorMsg.PRECHECK_ERROR_COMMON.value.zh
            if not self.vm_session.err_code:
                detail_status["err_code"] = ErrorCode.PRECHECK_ERROR_COMMON.value
            self.vm_session.update_detail_migrate_status(detail_status)
            log_msg = "vm migrate precheck failed, session id: {session_id}, " \
                      "error reason: {error_reason}" \
                      "".format(session_id=self.vm_session.session_id,
                                error_reason=str(e))
            logger.error(log_msg)
            logger.exception(e)
            return False
        else:
            return True

    def _check(self):
        raise Exception("forbidden define check function here")

    def _common_check(self):
        err_msg = ErrorMsg.SUCCESS.value
        err_code = ErrorCode.SUCCESS.value

        if self.vm_session.dst_vm_os_type not in InstanceOSType.list_type():
            err_msg = ErrorMsg.PRECHECK_ERROR_DST_VM_OS_TYPE_INVALID.value
            err_code = ErrorCode.PRECHECK_ERROR_DST_VM_OS_TYPE_INVALID.value

        if self.vm_session.dst_vm_image["nic_type"] not in SUPPORTED_NIC_TYPES:
            err_msg = ErrorMsg.PRECHECK_ERROR_DST_VM_NET_TYPE_INVALID.value
            err_code = ErrorCode.PRECHECK_ERROR_DST_VM_NET_TYPE_INVALID.value

        if self.vm_session.dst_vm_image["boot_loader"] not in InstanceBootLoaderType.list_type():
            err_msg = ErrorMsg.PRECHECK_ERROR_DST_VM_BOOT_LOADER_TYPE_INVALID.value
            err_code = ErrorCode.PRECHECK_ERROR_DST_VM_BOOT_LOADER_TYPE_INVALID.value

        if self.vm_session.dst_vm_image["block_bus"] not in [
            BLOCK_BUS_TYPE_VD,
            BLOCK_BUS_TYPE_SD,
            BLOCK_BUS_TYPE_HD
        ]:
            err_msg = ErrorMsg.PRECHECK_ERROR_DST_VM_BLOCK_BUS_TYPE_INVALID.value
            err_code = ErrorCode.PRECHECK_ERROR_DST_VM_BLOCK_BUS_TYPE_INVALID.value

        if self.vm_session.dst_vm_memory not in INSTANCE_MEMORY_TYPE:
            err_msg = ErrorMsg.PRECHECK_ERROR_DST_VM_MEMORY_VALUE_INVALID.value
            err_code = ErrorCode.PRECHECK_ERROR_DST_VM_MEMORY_VALUE_INVALID.value

        if self.vm_session.dst_vm_cpu not in INSTANCE_CPU_TYPE:
            err_msg = ErrorMsg.PRECHECK_ERROR_DST_VM_CPU_VALUE_INVALID.value
            err_code = ErrorCode.PRECHECK_ERROR_DST_VM_CPU_VALUE_INVALID.value

        if err_code == ErrorCode.SUCCESS.value:
            return

        self.vm_session.update_detail_migrate_status(
            dict(err_code=err_code, err_msg=err_msg.zh))
        log_msg = "migrate common precheck failed, session id: {session_id}, error " \
                  "reason :{error_reason}" \
                  "".format(session_id=self.vm_session.session_id,
                            error_reason=err_msg.en)
        logger.error(log_msg)
        raise Exception(log_msg)

    def clean(self):
        return self.vm_session.clean()


class ExportImageChecker(BaseChecker):
    """导出镜像模式迁移对应的检查器"""
    migrate_pattern = MigratePattern.EXPORT_IMAGE.value

    def __init__(self, vm_session):
        super(ExportImageChecker, self).__init__(vm_session)

    def _check(self):

        # 基本通用检查
        self._common_check()

        # 检查源虚拟机是否关机
        self._check_src_vm_poweroff()

    def _check_src_vm_poweroff(self):
        """检查源虚拟机是否关机"""
        status = self.vm_session.src_vm_status
        if status != SrcVmStatus.POWEREDOFF.value:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.PRECHECK_ERROR_SRC_VM_STATUS_INVALID.value,
                err_msg=ErrorMsg.PRECHECK_ERROR_SRC_VM_STATUS_INVALID.value.zh))

            log_msg = "the status of vm must be poweroff, session id: " \
                      "{session_id}, src vm id: {src_vm_id}, vm status: " \
                      "{src_vm_status}" \
                      "".format(src_vm_id=self.vm_session.src_vm_id,
                                session_id=self.vm_session.session_id,
                                src_vm_status=status)
            logger.error(log_msg)
            raise Exception(log_msg)


class UploadImageChecker(BaseChecker):
    """上传镜像模式迁移对应的检查器"""
    migrate_pattern = MigratePattern.UPLOAD_IMAGE.value

    def __init__(self, vm_session):
        super(UploadImageChecker, self).__init__(vm_session)

    def _check(self):

        # 基本通用检查
        self._common_check()

        # 检查源虚拟机上传路径下的字符串是否合法
        self._check_src_vm_nfs_path()

    def _check_src_vm_nfs_path(self):
        """检查源虚拟机上传路径下的字符串是否合法"""
        src_vm_nfs_path = self.vm_session.src_vm_nfs_path
        if not src_vm_nfs_path:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.PRECHECK_ERROR_STC_VM_NFS_PATH_EMPTY.value,
                err_msg=ErrorMsg.PRECHECK_ERROR_STC_VM_NFS_PATH_EMPTY.value.zh))
            log_msg = "src vm nfs path is empty,  session id: {session_id}" \
                      "".format(session_id=self.vm_session.session_id)
            logger.error(log_msg)
            raise Exception(log_msg)

        ovf_file_count = 0
        vmdk_file_count = 0
        ovf_file_path = ""

        nfs = NFSInterface(src_vm_nfs_path)
        for single_file in nfs.listdirs(""):
            if single_file.endswith('ovf'):
                ovf_file_path = os.path.join(src_vm_nfs_path, single_file)
                ovf_file_count += 1
            elif single_file.endswith('vmdk'):
                vmdk_file_count += 1
            else:
                pass

        # 检查ovf文件
        if ovf_file_count == 0:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.PRECHECK_ERROR_OVF_COUNT_INVALID.value,
                err_msg=ErrorMsg.PRECHECK_ERROR_OVF_COUNT_INVALID.value.zh))

            log_msg = "ovf file not found, src vm nfs path: %s"\
                      % src_vm_nfs_path
            logger.error(log_msg)
            raise Exception(log_msg)

        if ovf_file_count > 1:
            self.vm_session.update_detail_migrate_status(dict(
                err_code=ErrorCode.PRECHECK_ERROR_OVF_COUNT_INVALID.value,
                err_msg=ErrorMsg.PRECHECK_ERROR_OVF_COUNT_INVALID.value.zh))

            log_msg = "the count of ovf file exceed 1, ovf file count: %s, " \
                      "src vm nfs path: %s" \
                      % (ovf_file_count, src_vm_nfs_path)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 检查vmdk文件
        vmdk_data_count = 0
        ovf_file_content_xml = nfs.readfile(ovf_file_path)
        ovf_file_content_dict = xml_data_to_json_data(ovf_file_content_xml)
        Envelope = ovf_file_content_dict["Envelope"]
        References = Envelope["References"]
        File = References["File"]

        # 若源虚拟机有单个磁盘
        if isinstance(File, dict):
            vmdk_data_count = 1
            if vmdk_file_count != 1:
                self.vm_session.update_detail_migrate_status(dict(
                    err_code=ErrorCode.PRECHECK_ERROR_VMDK_COUNT_INVALID.value,
                    err_msg=ErrorMsg.PRECHECK_ERROR_VMDK_COUNT_INVALID.value.zh))

                log_msg = "the count of vmdk file not match vmdk data, vmdk " \
                          "data count: %s, vmdk file count: %s, src vm nfs" \
                          " path: %s" % \
                          (vmdk_data_count, vmdk_file_count, src_vm_nfs_path)
                logger.error(log_msg)
                raise Exception(log_msg)

        # 若源虚拟机有多个磁盘
        elif isinstance(File, list):
            for file_data in File:
                ovf_href = file_data["@ovf:href"]
                if ovf_href.endswith("vmdk"):
                    vmdk_data_count += 1
            if vmdk_data_count != vmdk_file_count:
                self.vm_session.update_detail_migrate_status(dict(
                    err_code=ErrorCode.PRECHECK_ERROR_VMDK_COUNT_INVALID.value,
                    err_msg=ErrorMsg.PRECHECK_ERROR_VMDK_COUNT_INVALID.value.zh))

                log_msg = "the count of vmdk file not match vmdk data, vmdk" \
                          " data count: %s, vmdk file count: %s, src vm nfs" \
                          " path: %s" % \
                          (vmdk_data_count, vmdk_file_count, src_vm_nfs_path)
                logger.error(log_msg)
                raise Exception(log_msg)
