# -*- coding: utf-8 -*-

import os
import telnetlib

from log.logger import logger

from fg.error import (
    Error,
    ErrorCode,
    ErrorMsg
)
from fg.return_tools import (
    return_error,
    return_success
)
from fg.constants import (
    ACTION_V2V_NAS_PARSE_VMS_FROM_NAS,
    ACTION_V2V_NAS_CHECK_NAS_CONNECTIVITY
)
from fg.resource_control.nas import (
    interface,
    vmware_img
)
from fg.uutils.utils_common import (
    is_contains_chinese,
    order_list_and_paginate
)


def handle_parse_vms_from_nas(req):
    """从NAS服务器中解析虚拟机信息"""
    logger.debug('handle parse vms from nas start, {}'.format(req))
    url = req.get("image_addr")
    offset = req.get("offset", 0)
    limit = req.get("limit", 10)
    sort_key = req.get("sort_key", "template")
    reverse = req.get("reverse", False)

    # 中文检查
    is_cn = is_contains_chinese(url)
    if is_cn:
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_INVAILD_NFS_URL_ADDRESS.value,
                                  ErrorMsg.ERR_MSG_NAS_INVAILD_NFS_URL_ADDRESS.value))

    # 初始化客户端
    nfs_client = interface.NFSClient(url)
    if not nfs_client.mount():
        logger.error("nfs url check connectivity failed, url: %s" % url)
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_NFS_URL_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_NAS_NFS_URL_NOT_CONNECT.value))

    datas = []
    vm_dirs = nfs_client.list_dirs(".")
    for vm_dir in vm_dirs:
        try:
            vm_upload_path = os.path.join(url, vm_dir)
            stat_info = nfs_client.stat_file(vm_dir)
            if stat_info.get("nlink") == 1:
                continue

            vm_file_list = nfs_client.list_dirs(vm_dir)
            vm_ovf_path = ''
            ovf_count = 0
            vmdk_count = 0

            for vm_file in vm_file_list:
                if vm_file.endswith('ovf'):
                    vm_ovf_path = os.path.join(vm_dir, vm_file)
                    ovf_count += 1
                elif vm_file.endswith("vmdk"):
                    vmdk_count += 1
            if not vm_ovf_path:
                logger.error("ovf file not found in vm image path: %s "
                             "" % vm_upload_path)
                continue

            if ovf_count > 1:
                logger.error("the count of ovf file is {ovf_count}, vm upload "
                             "path: {vm_upload_path}"
                             "".format(vm_upload_path=vm_upload_path,
                                       ovf_count=ovf_count))
                continue

            ovf_xml = nfs_client.read_file(vm_ovf_path)
            vm_img = vmware_img.VmWareImg(ovf_xml, vm_upload_path)
            vm = vm_img.parse_vm_dict()

            vmdk_img_ct = vm_img.get_vmdk_file_count()
            if vmdk_img_ct != vmdk_count:
                logger.error("vm vmdk file: %s not match image vmdk: %s" % (
                    vmdk_img_ct, vmdk_count))
                continue

            datas.append(vm)
        except Exception as e:
            logger.exception("get vm image path failed, url: %s, error: %s"
                             "" % (url, e))
            continue
    try:
        result_list, total = order_list_and_paginate(datas, sort_key, offset,
                                                     limit, reverse)
    except Exception as e:
        logger.exception("pageinate error, data: {data}, error: {e}"
                         "".format(data=datas, e=e))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_PARSE_VMS_FROM_NFS_PAGINATE_ERROR.value,
                                  ErrorMsg.ERR_MSG_NAS_PARSE_VMS_FROM_NFS_PAGINATE_ERROR.value))

    return return_success(req, None, datas={"src_vm_set": result_list,
                                            "total_count": total})


def handle_check_nas_connectivity(req):
    """检查NAS的联通性"""
    logger.debug('handle check nas connectivity start, {}'.format(req))
    url = req.get("image_addr")
    port = req.get("port", 2049)

    # 中文检查
    is_cn = is_contains_chinese(url)
    if is_cn:
        logger.error("url address of url contain chinese, url: %s" % url)
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_INVAILD_NFS_URL_ADDRESS.value,
                                  ErrorMsg.ERR_MSG_NAS_INVAILD_NFS_URL_ADDRESS.value))

    # 统一nfs路径格式
    if url.startswith("nfs://"):
        nfs_arr = url.split("nfs://")
        if len(nfs_arr) == 2:
            url = nfs_arr[1]

    # 解析主机地址
    host = ""
    if len(url.split("/")) > 0:
        host = url.split("/")[0]

    # 主机检查
    ret = os.system("ping {host} -c 1".format(host=host))
    if ret != 0:
        logger.error("nfs connectivity check failed, url: %s, host, %s, port: "
                     "%s, reason: host is cot connect" % (url, host, port))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_NFS_URL_IP_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_NAS_NFS_URL_IP_NOT_CONNECT.value))

    # 端口检查
    try:
        tn = telnetlib.Telnet()
        tn.open(host, port, timeout=2)
    except Exception:
        logger.error("nfs connectivity check failed, url: %s, host, %s, port: "
                     "%s, reason: port is cot connect" % (url, host, port))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_NFS_URL_PORT_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_NAS_NFS_URL_PORT_NOT_CONNECT.value))

    # URL地址检查
    nfs_client = interface.NFSClient(url)
    if not nfs_client.mount():
        logger.error("nfs connectivity check failed, url: %s, port: %s"
                     "" % (url, port))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_NAS_NFS_URL_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_NAS_NFS_URL_NOT_CONNECT.value))

    return return_success(req, None, data=True)


HANDLER_MAP = {
    ACTION_V2V_NAS_PARSE_VMS_FROM_NAS: handle_parse_vms_from_nas,
    ACTION_V2V_NAS_CHECK_NAS_CONNECTIVITY: handle_check_nas_connectivity
}
