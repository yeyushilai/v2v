# -*- coding: utf-8 -*-

import re

from log.logger import logger

from fg.return_tools import (
    return_error,
    return_success
)
from fg.error import (
    Error,
    ErrorCode,
    ErrorMsg
)
from fg.constants import (
    # 动作
    ACTION_V2V_SRC_PLATFORM_CHECK_SRC_PLATFORM_CONNECTIVITY,
    ACTION_V2V_SRC_PLATFORM_ADD_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_DELETE_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM,
    ACTION_V2V_SRC_PLATFORM_UPDATE_SRC_PLATFORM,

    # 迁移要素
    SrcPlatformType,
    SrcPlatformStatus,
    SrcPlatformVmStatus,
    CONNECTION_STATUS_MAPPER,
    MigrateStatus
)
from fg.uutils.pg.interface import (
    TableSrcPlatform,
    TableMigrateTask,
    TableVm
)
from fg.uutils.utils_common import (
    order_list_and_paginate,
    generate_platform_id,
    is_contains_chinese
)
from fg.resource_control.vmware_vsphere import VMwareVSphere

tb_platform_obj = TableSrcPlatform()
tb_task_obj = TableMigrateTask()
tb_vm_obj = TableVm()


def common_check(func):
    def inner(*args, **kwargs):
        req = args[0]

        platform_type = req.get("type")
        if not platform_type:
            return func(*args, **kwargs)

        # 源平台类型检测
        if platform_type != SrcPlatformType.VMWARE.value:
            logger.exception("the type of src platform not support, platform "
                             "type: %s" % platform_type)
            return return_error(req,
                                Error(ErrorCode.ERR_CODE_SRC_PLATFORM_INVALID_SRC_PLATFORM_TYPE.value,
                                      ErrorMsg.ERR_MSG_SRC_PLATFORM_INVALID_SRC_PLATFORM_TYPE.value))
        return func(*args, **kwargs)

    return inner


@common_check
def handle_check_src_platform_connectivity(req):
    """检查和源平台的连通性"""
    logger.debug('handle check src platform connectivity start, {}'.format(req))
    account = dict()
    account["ip"] = req.get("ip")
    account["port"] = req.get("port")
    account["username"] = req.get("username")
    account["encrypt_password"] = req.get("encrypt_password")
    vs = VMwareVSphere(account)

    try:
        is_connected = vs.is_connected()
    except BaseException as e:
        logger.exception("connect to src platform failed, platform id: %s, "
                         "error reason: %s" % (account["ip"], e))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value))

    if not is_connected:
        logger.error("connect to src platform failed, platform id: %s, error "
                     "reason: can not connect" % account["ip"])
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value))

    return return_success(req, None, datas=dict(is_connect=True, err_msg=""))


@common_check
def handle_add_src_platform(req):
    """添加源平台"""
    logger.debug('handle add src platform start, {}'.format(req))
    user_id = req["sender"].get("user_id")

    account = dict()
    platform_name = req.get("name")
    platform_type = req.get("type")
    platform_ip = account["ip"] = req.get("ip")
    platform_port = account["port"] = req.get("port")
    platform_user = account["username"] = req.get("username")
    platform_password = account["encrypt_password"] = req.get(
        "encrypt_password")
    vs = VMwareVSphere(account)

    # 重复性检测
    platforms = tb_platform_obj.list_src_platform(user_id=user_id,
                                                  platform_ip=platform_ip,
                                                  platform_user=platform_user)
    exists_platform_list = [platform["platform_ip"] for platform in platforms]
    if platform_ip in exists_platform_list:
        logger.error("platform has aleady exists, platform ip: "
                     "{platform_ip}".format(platform_ip=platform_ip))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_EXISTS.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_EXISTS.value))

    # 联通性检测
    try:
        is_connected = vs.is_connected()
    except BaseException as e:
        logger.exception("connect to src platform failed, platform id: %s, "
                         "error reason: %s" % (account["ip"], e))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value))
    if not is_connected:
        logger.error("connect to src platform failed, platform id: %s, error "
                     "reason: can not connect" % account["ip"])
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value))
    status = SrcPlatformStatus.MIGRATE_SUPPORT.value

    # 从vsphere平台获取信息
    resource = vs.list_resource()
    version = vs.vi.version

    # 添加vsphere
    platform_id = generate_platform_id()
    tb_platform_obj.create_src_platform(
        platform_id, user_id, platform_type, platform_ip,
        platform_port, platform_user, platform_password,
        platform_name, version, status, resource)

    return return_success(req, None, datas="ok")


@common_check
def handle_describe_src_platform(req):
    """展示所有源平台的基本信息"""
    logger.debug('handle describe src platform start, {}'.format(req))
    user_id = req["sender"].get("user_id")

    platforms = tb_platform_obj.list_src_platform(user_id)

    datas = list()
    for platform in platforms:
        temp_dict = dict()
        temp_dict["type"] = platform["platform_type"]
        temp_dict["name"] = platform["platform_name"]
        temp_dict["id"] = platform["platform_id"]
        temp_dict["ip"] = platform["platform_ip"]
        temp_dict["port"] = platform["platform_port"]
        temp_dict["version"] = platform["platform_version"]
        temp_dict["username"] = platform["platform_user"]
        temp_dict["encrypt_password"] = platform["platform_password"]
        temp_dict["resource"] = platform["resource"]
        vs = VMwareVSphere(temp_dict)

        # 源平台的状态，实时获取
        is_connected = False
        try:
            is_connected = vs.is_connected()
        except BaseException as e:
            logger.exception(
                "connect to src platform failed, platform id: %s, "
                "error reason: %s" % (temp_dict["id"], e))

        if not is_connected:
            logger.error(
                "connect to src platform failed, platform id: %s, error "
                "reason: can not connect" % temp_dict["id"])

        temp_dict["status"] = CONNECTION_STATUS_MAPPER[is_connected]

        datas.append(temp_dict)

    return return_success(req, None, datas=datas)


@common_check
def handle_describe_src_platform_vm(req):
    """展示源平台中的虚拟机信息"""
    logger.debug('handle describe src platform vm start, {}'.format(req))

    platform_ip = req.get("ip")
    platform_port = req.get("port")
    platform_user = req.get("username")
    platform_password = req.get("encrypt_password")

    datacenter_name = req.get("datacenter_name")
    search_word = req.get("search_word")
    if search_word and is_contains_chinese(search_word):
        search_word = search_word.encode("utf-8")
    offset = req.get("offset", 0)
    limit = req.get("limit", 10)
    sort_key = req.get("sort_key", "template")
    reverse = req.get("reverse", False)
    migrated = req.get("migrated")
    user_id = req["sender"].get("user_id")

    # 获取源平台中的虚拟机信息
    account = dict()
    account["ip"] = platform_ip
    account["port"] = platform_port
    account["username"] = platform_user
    account["encrypt_password"] = platform_password
    vs = VMwareVSphere(account)
    try:
        vm_info_list = vs.list_datacenter_vm(datacenter_name)
    except Exception as e:
        logger.exception("list vm in datacenter failed, datacenter name: "
                         "{datacenter_name}, ip: {ip}, error reason: "
                         "{error}".format(datacenter_name=datacenter_name,
                                          ip=account["ip"],
                                          error=str(e)))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_LIST_VM_IN_SRC_PLATFORM_ERROR.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_LIST_VM_IN_SRC_PLATFORM_ERROR.value))

    migrated_vm = tb_vm_obj.list_vm(status=MigrateStatus.COMPLETED.value,
                                    user_id=user_id,
                                    distinct=True)
    migrated_vm_ids = [src_vm.get("src_vm_id") for src_vm in migrated_vm]

    data_list = []
    for vm_info in vm_info_list:
        # 根据是否迁移过滤
        if migrated != (vm_info["uuid"] in migrated_vm_ids):
            continue

        # 搜索过滤
        if search_word:
            match_len = re.findall(r'%s.*' % search_word, vm_info["name"])
            if len(match_len) == 0:
                continue

        # 不受支持的虚拟机，标记具体原因
        if vm_info["is_template"]:
            vm_info["reason"] = "虚拟机为模板虚拟机，不支持迁移"
        if not vm_info["os_type"]:
            vm_info["reason"] = "虚拟机操作系统类型未知，不支持迁移"
        if vm_info["status"] != SrcPlatformVmStatus.POWEREDOFF.value:
            vm_info["reason"] = "虚拟机非关机状态，不支持迁移"
        data_list.append(vm_info)

    # 排序，过滤，切片
    try:
        result_list, total = order_list_and_paginate(data_list, sort_key,
                                                     offset, limit, reverse)
    except Exception as e:
        logger.exception("pageinate error, data: {data}, error: {e}"
                         "".format(data=data_list, e=e))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM_PAGINATE_ERROR.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM_PAGINATE_ERROR.value))

    return return_success(req, None, datas=result_list, total=total)


@common_check
def handle_update_src_platform(req):
    """更新源平台"""
    logger.debug('handle update src platform start, {}'.format(req))
    platform_id = req.get("platform_id")

    account = dict()
    platform_ip = account["ip"] = req.get("ip")
    platform_port = account["port"] = req.get("port")
    platform_username = account["username"] = req.get("username")
    platform_password = account["encrypt_password"] = req.get("encrypt_password")
    platform_name = req.get("name")
    vs = VMwareVSphere(account)

    # 存在性检测
    platform_info = tb_platform_obj.query_src_platform(platform_id)
    if not platform_info:
        logger.exception("query src platform failed, platform id: %s, "
                         "error reason: platform id not exists"
                         % platform_id)
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_EXISTS.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_EXISTS.value))

    # 联通性检测
    try:
        is_connected = vs.is_connected()
    except BaseException as e:
        logger.exception("connect to src platform failed, platform id: %s, "
                         "error reason: %s" % (account["ip"], e))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value))

    if not is_connected:
        logger.error("connect to src platform failed, platform id: %s, error "
                     "reason: can not connect" % account["ip"])
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT.value))
    status = SrcPlatformStatus.MIGRATE_SUPPORT.value

    # 同步更新资源、版本信息
    resource = vs.list_resource()
    version = vs.vi.version

    # 更新源平台数据到数据库
    tb_platform_obj.update_src_platform(platform_id, platform_ip, platform_port,
                                        platform_username, platform_password,
                                        platform_name, status, resource, version)

    return return_success(req, None, datas="ok")


@common_check
def handle_delete_src_platform(req):
    """删除源平台"""
    logger.debug('handle delete src platform start, {}'.format(req))
    platform_id = req.get("platform_id")
    user_id = req["sender"].get("user_id")

    # 存在性检测
    platform_info = tb_platform_obj.query_src_platform(platform_id)
    if not platform_info:
        logger.exception("query src platform failed, platform id: %s, "
                         "error reason: platform id not exists"
                         % platform_id)
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_EXISTS.value,
                                  ErrorMsg.ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_EXISTS.value))

    # 检查是否存在关联的未完成迁移的虚拟机
    tasks = tb_task_obj.list_migration_task(user_id=user_id,
                                            src_platform_id=platform_id)
    task_id_list = [task_info["task_id"] for task_info in tasks]
    if task_id_list:
        vm_list = tb_vm_obj.list_vm(user_id=user_id, task_id=task_id_list)
        vm_id_info_map = {vm_info["session_id"]: vm_info for vm_info in vm_list}

        for session_id, vm_info in vm_id_info_map.items():
            vm_status = vm_info["status"]
            if vm_status != MigrateStatus.COMPLETED.value:
                logger.exception("relative working migration task exists, task "
                                 "id: {task_id}, session id: {session_id}, "
                                 "platform id: {platform_id}"
                                 "".format(task_id=vm_info["task_id"],
                                           session_id=session_id,
                                           platform_id=platform_id))
                return return_error(req,
                                    Error(ErrorCode.ERR_CODE_SRC_PLATFORM_RELATIVE_WORKING_MIGRATION_TASK_EXISTS.value,
                                          ErrorMsg.ERR_MSG_SRC_PLATFORM_RELATIVE_WORKING_MIGRATION_TASK_EXISTS.value))

    tb_platform_obj.delete_src_platform(platform_id)

    return return_success(req, None, datas="ok")


HANDLER_MAP = {
    ACTION_V2V_SRC_PLATFORM_CHECK_SRC_PLATFORM_CONNECTIVITY: handle_check_src_platform_connectivity,
    ACTION_V2V_SRC_PLATFORM_ADD_SRC_PLATFORM: handle_add_src_platform,
    ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM: handle_describe_src_platform,
    ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM: handle_describe_src_platform_vm,
    ACTION_V2V_SRC_PLATFORM_UPDATE_SRC_PLATFORM: handle_update_src_platform,
    ACTION_V2V_SRC_PLATFORM_DELETE_SRC_PLATFORM: handle_delete_src_platform
}
