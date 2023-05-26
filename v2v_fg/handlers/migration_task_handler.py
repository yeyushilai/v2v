# -*- coding: utf-8 -*-

from collections import defaultdict

from log.logger import logger
from db.data_types import (
    SearchWordType,
    NotType
)

from fg import context
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
    # action
    ACTION_V2V_MIGRATION_TASK_CREATE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_UPDATE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DELETE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DETAIL_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_VM,

    # iaas
    INSTANCE_MEMORY_TYPE,
    INSTANCE_CPU_TYPE,
    QUOTA_INSTANCE_ENUM_AND_TYPE_MAP,
    QUOTA_INSTANCE_ENUM_AND_MEMORY_TYPE_MAP,
    QUOTA_INSTANCE_ENUM_AND_CPU_TYPE_MAP,
    QUOTA_VOLUME_ENUM_AND_NAME_MAP,

    # migration
    MigrateStatus,

    # src platform
    SrcPlatformType,

    # instance
    InstanceOSType
)
from fg.uutils.pg.interface import (
    TableSrcPlatform,
    TableMigrateTask,
    TableVm
)
from fg.uutils.utils_common import (
    generate_image_id,
    generate_task_id,
    generate_session_id
)

ctx = context.instance()
tb_platform_obj = TableSrcPlatform()
tb_task_obj = TableMigrateTask()
tb_vm_obj = TableVm()


def handle_create_migration_task(req):
    """创建迁移任务"""
    logger.debug('handle create migration task start, {}'.format(req))
    logger.info(req)
    console_id = req["sender"].get("console_id")
    user_id = req["sender"].get("user_id")
    vms_config = req.get("vms_config")
    owner_id = req.get("owner_id")
    task_name = req.get("task_name")
    task_desc = req.get("task_desc")
    task_pattern = req.get("task_pattern")
    src_platform_id = req.get("src_platform_id")
    src_datacenter_name = req.get("src_datacenter_name")
    dst_region_id = req.get("dst_region_id")
    dst_zone_id = req.get("dst_zone_id")
    dst_node_id = req.get("dst_node_id")
    submit = req.get("submit")

    # 编排标准的迁移任务数据
    standard_task_config = {
        "console_id": console_id,
        "owner_id": owner_id,
        "task_name": task_name,
        "task_desc": task_desc,
        "user_id": user_id,
        "task_pattern": task_pattern,
        "dst_region_id": dst_region_id,
        "dst_zone_id": dst_zone_id
    }
    if src_platform_id:
        standard_task_config["src_platform_id"] = src_platform_id
    if src_datacenter_name:
        standard_task_config["src_datacenter_name"] = src_datacenter_name
    if dst_node_id:
        standard_task_config["dst_node_id"] = dst_node_id
    else:
        standard_task_config["dst_node_id"] = "auto"

    # 编排标准的迁移任务中的虚拟机数据
    standard_vms_config = list()
    task_total_rs_usage = defaultdict(int)
    task_total_quota_usage = defaultdict(int)

    priority = len(vms_config)
    for vm_config in vms_config:
        standard_vm_config = {
            "priority": priority,
            "user_id": user_id,
            "status": MigrateStatus.READY.value,
            "process": 0,
            "step": {},
            "src_vm_id": vm_config.get("src_vm_id"),
            "src_vm_cpu_core": vm_config.get("src_vm_cpu_core"),
            "src_vm_memory": vm_config.get("src_vm_memory"),
            "src_vm_folder": vm_config.get("src_vm_folder"),
            "src_vm_nfs_path": vm_config.get("src_vm_nfs_path") or "",
            "src_vm_create_time": vm_config.get("src_vm_create_time"),
            "src_vm_os_name": vm_config.get("src_vm_os_name"),
            "src_vm_os_type": vm_config.get("src_vm_os_type"),
            "src_vm_disk": vm_config.get("src_vm_disk"),
            "src_vm_net": vm_config.get("src_vm_net"),
            "dst_vm_name": vm_config.get("dst_vm_name"),
            "dst_vm_os_name": vm_config.get("src_vm_os_name"),
            "dst_vm_image": vm_config.get("dst_vm_image"),
            "dst_vm_net": vm_config.get("dst_vm_net")
        }

        src_vm_name = vm_config.get("src_vm_name")
        dst_vm_disk = vm_config.get("dst_vm_disk")
        dst_vm_os_type = vm_config.get("dst_vm_os_type")
        dst_vm_os_disk = vm_config.get("dst_vm_os_disk")
        dst_vm_data_disk = vm_config.get("dst_vm_data_disk")
        dst_vm_cpu_core = vm_config["dst_vm_cpu_core"]
        dst_vm_memory = vm_config["dst_vm_memory"]

        # 检查目标虚拟机的类型
        if dst_vm_os_type not in InstanceOSType.list_type():
            logger.error("dst vm os type is invalid, os type: {os_type}, src "
                         "vm name: {src_vm_name}"
                         "".format(os_type=dst_vm_os_type,
                                   src_vm_name=src_vm_name))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_INVALID_OS_TYPE.value,
                                    ErrorMsg.ERR_MSG_IAAS_INVALID_OS_TYPE.value))

        # 检查硬件的基本类型
        if dst_vm_memory not in INSTANCE_MEMORY_TYPE:
            logger.error("dst vm memory type is invalid, memory type: "
                         "{memory_type}, src vm name: {src_vm_name}"
                         "".format(memory_type=dst_vm_memory,
                                   src_vm_name=src_vm_name))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_INVALID_MEMORY_TYPE.value,
                                    ErrorMsg.ERR_MSG_IAAS_INVALID_MEMORY_TYPE.value))
        if dst_vm_cpu_core not in INSTANCE_CPU_TYPE:
            logger.error("dst vm cpu type is invalid, cpu type: {cpu_type} "
                         ", src vm name: {src_vm_name}"
                         "".format(cpu_type=dst_vm_cpu_core,
                                   src_vm_name=src_vm_name))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_INVALID_CPU_TYPE.value,
                                    ErrorMsg.ERR_MSG_IAAS_INVALID_CPU_TYPE.value))

        # 统计硬件资源使用量
        dst_vm_disk_total_size = sum(
            disk_info["size"] for disk_info in dst_vm_disk)
        task_total_rs_usage["disk"] += dst_vm_disk_total_size
        task_total_rs_usage["cpu"] += dst_vm_cpu_core
        task_total_rs_usage["memory"] += dst_vm_memory

        # 统计硬件资源配额占用量
        instance_class = vm_config["dst_vm_type"]
        cpu_type = QUOTA_INSTANCE_ENUM_AND_CPU_TYPE_MAP.get(instance_class)
        memory_type = QUOTA_INSTANCE_ENUM_AND_MEMORY_TYPE_MAP.get(
            instance_class)
        instance_type = QUOTA_INSTANCE_ENUM_AND_TYPE_MAP.get(instance_class)
        os_disk_type = QUOTA_VOLUME_ENUM_AND_NAME_MAP.get(
            dst_vm_os_disk["type"])
        task_total_quota_usage["image"] += 1
        task_total_quota_usage[instance_type] += 1
        task_total_quota_usage[cpu_type] += dst_vm_cpu_core
        task_total_quota_usage[memory_type] += dst_vm_memory

        task_total_quota_usage[os_disk_type] += 1
        if dst_vm_data_disk:
            data_disk_type = QUOTA_VOLUME_ENUM_AND_NAME_MAP.get(
                dst_vm_data_disk["type"])
            task_total_quota_usage[data_disk_type] += len(dst_vm_disk) - 1
            standard_vm_config["dst_vm_data_disk"] = dst_vm_data_disk

        standard_vm_config["src_vm_name"] = src_vm_name
        standard_vm_config["dst_vm_disk"] = dst_vm_disk
        standard_vm_config["dst_vm_os_type"] = dst_vm_os_type
        standard_vm_config["dst_vm_os_disk"] = dst_vm_os_disk
        standard_vm_config["dst_vm_cpu_core"] = dst_vm_cpu_core
        standard_vm_config["dst_vm_memory"] = dst_vm_memory
        standard_vm_config["dst_vm_type"] = instance_class

        standard_vms_config.append(standard_vm_config)
        priority -= 1

    # 检查网络资源是否充足
    vxnet_id_and_ip_map = defaultdict(list)
    for standard_vm_config in standard_vms_config:
        dst_vm_net = standard_vm_config['dst_vm_net']
        assert isinstance(dst_vm_net, list)
        for net_info in dst_vm_net:
            vxnet_id = net_info["vxnet_id"]
            ip = net_info["ip"]
            if not ip:
                continue
            if ip not in vxnet_id_and_ip_map[vxnet_id]:
                vxnet_id_and_ip_map[vxnet_id].append(ip)
            else:
                logger.error("ip conflicts, src vm name: %s, vxnet id and "
                             "ip map: %s, ip: %s"
                             "" % (standard_vm_config["src_vm_name"],
                                   vxnet_id_and_ip_map,
                                   ip))
                return return_error(req,
                                    Error(
                                        ErrorCode.ERR_CODE_MIGRATION_VM_INNER_IP_CONFLICTS.value,
                                        ErrorMsg.ERR_MSG_MIGRATION_VM_INNER_IP_CONFLICTS.value))

    # 检查目标用户配额是否充足
    quota_left_res = ctx.iaas.get_quota_left(task_total_quota_usage.keys(),
                                             owner_id)
    logger.info("quota left res: {quota_left_res}, resource type: "
                "{resource_type}, owner id: {owner_id}"
                "".format(quota_left_res=quota_left_res,
                          owner_id=owner_id,
                          resource_type=task_total_quota_usage.keys()))
    assert isinstance(quota_left_res, dict)
    assert quota_left_res.get("ret_code") == 0
    assert isinstance(quota_left_res.get("quota_left_set"), list)
    for quota_left_dict in quota_left_res.get("quota_left_set"):
        resource_type = quota_left_dict.get("resource_type")
        quota_usage = task_total_quota_usage.get(resource_type, 0)
        quota_left = quota_left_dict.get("left")
        if quota_usage > quota_left:
            over = quota_usage - quota_left
            logger.error("quota check failed, owner id: {owner_id}, resource "
                         "type: {resource_type}, over value: {over}, quota "
                         "usage: {quota_usage}, quota left: {quota_left}"
                         "".format(owner_id=owner_id,
                                   resource_type=resource_type,
                                   over=over,
                                   quota_usage=quota_usage,
                                   quota_left=quota_left))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_USER_QUOTA_NOT_ENOUGH.value,
                                    ErrorMsg.ERR_MSG_IAAS_USER_QUOTA_NOT_ENOUGH.value),
                                data=task_total_quota_usage)

    # 检查节点资源是否充足
    dst_node_id = standard_task_config["dst_node_id"]
    if dst_node_id != "auto":
        ret = ctx.iaas.describe_bots(bots=[dst_node_id],
                                     zone=dst_zone_id,
                                     status=["active"])
        free_disk = 0
        free_memory = 0
        free_vcpu = 0
        if ret.get("ret_code") == 0 and ret.get("bot_set"):
            for bot in ret.get("bot_set"):
                free_disk += bot.get("free_disk")
                free_memory += bot.get("free_memory")
                free_vcpu += bot.get("free_vcpu")
        else:
            logger.error("bots info is empty, dst zone id: {dst_zone_id}, dst"
                         " node id: {dst_node_id}"
                         "".format(dst_zone_id=dst_zone_id,
                                   dst_node_id=dst_node_id))
            return return_error(req,
                                Error(ErrorCode.ERR_CODE_IAAS_HYPER_DATA_EMPTY.value,
                                      ErrorMsg.ERR_MSG_IAAS_HYPER_DATA_EMPTY.value))

        if task_total_rs_usage["cpu"] >= free_vcpu:
            logger.error("cpu resource check failed, resource usage: "
                         "{resource_usage}, resource free: {resource_free}"
                         "".format(owner_id=owner_id,
                                   resource_usage=task_total_rs_usage["cpu"],
                                   resource_free=free_vcpu))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_HYPER_FREE_CPU_NOT_ENOUGH.value,
                                    ErrorMsg.ERR_MSG_IAAS_HYPER_FREE_CPU_NOT_ENOUGH.value))

        if task_total_rs_usage["memory"] >= free_memory:
            logger.error("memory resource check failed, resource usage: "
                         "{resource_usage}, resource free: {resource_free}"
                         "".format(owner_id=owner_id,
                                   resource_usage=task_total_rs_usage[
                                       "memory"],
                                   resource_free=free_memory))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_HYPER_FREE_MEMORY_NOT_ENOUGH.value,
                                    ErrorMsg.ERR_MSG_IAAS_HYPER_FREE_MEMORY_NOT_ENOUGH.value))

        if task_total_rs_usage["disk"] >= free_disk:
            logger.error("disk resource check failed, resource usage: "
                         "{resource_usage}, resource free: {resource_free}"
                         "".format(owner_id=owner_id,
                                   resource_usage=task_total_rs_usage["disk"],
                                   resource_free=free_disk))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_IAAS_HYPER_FREE_DISK_NOT_ENOUGH.value,
                                    ErrorMsg.ERR_MSG_IAAS_HYPER_FREE_DISK_NOT_ENOUGH.value))

    # 单纯的检查不创建任务，直接返回
    if not submit:
        return return_success(req, None, data="ok")

    # 创建迁移任务（写表）
    try:
        task_id = generate_task_id()
        standard_task_config["task_id"] = task_id
        tb_task_obj.create_migration_task(standard_task_config)

        for standard_vm_config in standard_vms_config:
            standard_vm_config["task_id"] = task_id
            standard_vm_config["dst_vm_image"][
                "image_id"] = generate_image_id()
            standard_vm_config["session_id"] = generate_session_id()
            tb_vm_obj.create_vm(standard_vm_config)

    except Exception as e:
        log_msg = "create migrate task failed, task config: {task_config}, " \
                  "vms config: {vms_config}, reason: {reason}" \
                  "".format(task_config=standard_task_config,
                            vms_config=standard_vms_config,
                            reason=str(e))
        logger.exception(log_msg)
        return return_error(req,
                            Error(
                                ErrorCode.ERR_CODE_MIGRATION_TASK_CREATE_MIGRATION_TASK_ERROE.value,
                                ErrorMsg.ERR_MSG_MIGRATION_TASK_CREATE_MIGRATION_TASK_ERROE.value))

    return return_success(req, None, datas=dict(task_id=task_id))


def handle_update_migration_task(req):
    """更新迁移任务，逻辑尚未实现"""
    logger.debug('handle update migration task start, {}'.format(req))
    platform_id = req.get("platform_id")
    return return_success(req, None, datas={"platform_id": platform_id})


def handle_delete_migration_task(req):
    """删除迁移任务"""
    logger.debug('handle delete migration task start, {}'.format(req))
    task_ids = req.get("task_ids")
    user_id = req.get("user_id")

    # 存在性检查
    task_list = tb_task_obj.list_migration_task(user_id=user_id, task_id=task_ids)
    task_dict = {}
    for task_id in task_ids:
        for task_info in task_list:
            if task_id == task_info["task_id"]:
                task_dict[task_id] = task_info
                break
        else:
            logger.error("migration task not exist, task id: {}".format(task_id))
            return return_error(req,
                                Error(ErrorCode.ERR_CODE_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS.value,
                                      ErrorMsg.ERR_MSG_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS.value))

    success_list = []
    failed_list = []
    for task_id, task_info in task_dict.items():

        # 任务中的虚拟机合法性检测(不合理会统计跳过)
        vm_list = tb_vm_obj.list_vm(
            task_id=task_id,
            status=NotType(MigrateStatus.list_support_delete_status()))
        if vm_list:
            logger.error("the vm which not delete-supported exists, "
                         "vm list: {vm_list}, task id: {task_id}"
                         "".format(vm_list=vm_list, task_id=task_id))
            failed_list.append(task_id)
            continue

        # 执行删除操作并记录是否成功
        condition = {"task_id": task_id}
        columns = {"is_delete": True}
        vm_cnt = tb_vm_obj.update_vm(condition, columns)
        task_cnt = tb_task_obj.update_migration_task(condition, columns)

        if task_cnt > 0 and vm_cnt > 0:
            success_list.append(task_id)
        else:
            logger.error("execute delete task failed, task id: {task_id}"
                         "".format(task_id=task_id))
            failed_list.append(task_id)

    logger.info("delete migration task end, success list: {success_list},  "
                "failed list: {failed_list}"
                "".format(success_list=success_list, failed_list=failed_list))
    if len(task_ids) == len(success_list):
        return return_success(req, dict(data="ok"))
    else:
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_MIGRATION_TASK_DELETE_PART_MIGRATION_TASK_ERROE.value,
                                  ErrorMsg.ERR_MSG_MIGRATION_TASK_DELETE_PART_MIGRATION_TASK_ERROE.value,
                                  success_list=success_list,
                                  failed_list=failed_list))


def handle_describe_migration_task(req):
    """获取迁移任务列表"""
    logger.debug('handle describe migration task start, {}'.format(req))
    user_id = req["sender"].get("user_id")
    offset = req.get("offset", 0)
    limit = req.get("limit", 10)
    sort_key = req.get("sort_key", "create_time")
    reverse = req.get("reverse", True)
    search_word = req.get("search_word")
    search_word = SearchWordType(search_word) if search_word else search_word

    # 列举所有迁移任务（排序、搜索、分页功能暂不支持）
    task_list = tb_task_obj.list_migration_task(user_id=user_id,
                                                limit=limit,
                                                offset=offset,
                                                sort_key=sort_key,
                                                reverse=reverse,
                                                search_word=search_word)
    if not task_list:
        logger.info("migration task list is empty, user id: %s, search word: "
                    "%s" % (user_id, search_word))
        datas = {"task_set": [], "total_count": 0}
        return return_success(req, None, datas=datas)

    # 列举所有用户信息
    owner_list = []
    for task_info in task_list:
        if task_info["owner_id"] not in owner_list:
            owner_list.append(task_info["owner_id"])
    owner_dict = {}
    user_ret = ctx.iaas.desc_users(users=owner_list)
    if user_ret and user_ret.get("ret_code") == 0:
        user_set = user_ret.get("user_set")
        if user_ret:
            for user_data in user_set:
                owner_dict[user_data.get("user_id")] = user_data

    # 列举所有源平台信息
    platform_list = tb_platform_obj.list_src_platform(user_id=user_id)
    platform_dict = {platform_info["platform_id"]: platform_info
                     for platform_info in platform_list}

    # 列举所有虚拟机信息
    vm_list = tb_vm_obj.list_vm(user_id=user_id)
    vm_dict = {vm_info["session_id"]: vm_info
               for vm_info in vm_list}

    task_set = []
    for task_info in task_list:
        task_id = task_info.get("task_id")

        # 源平台信息
        src_platform_id = task_info.get("src_platform_id")
        platform_info = platform_dict.get("src_platform_id")
        platform_name = platform_info["platform_name"] if platform_info else ""

        # 统计全部数量、已经迁移数量、正在迁移中数量
        total_vm_list = []
        migrated_vm_list = []
        processing_vm_list = []
        for vm_info in vm_dict.values():
            if task_id != vm_info["task_id"]:
                continue
            total_vm_list.append(vm_info)
            if vm_info["status"] == MigrateStatus.COMPLETED.value:
                migrated_vm_list.append(vm_info)
            if vm_info["status"] in MigrateStatus.list_processing_migrate_status():
                processing_vm_list.append(vm_info)

        # 目标用户信息
        owner_id = task_info.get("owner_id")
        owner_name = owner_dict[owner_id].get("user_name", "")

        # 编排数据
        task_data = {
            "task_id": task_id,
            "task_name": task_info.get("task_name"),
            "task_pattern": task_info.get("task_pattern"),
            "create_time": task_info.get("create_time"),
            "user_id": user_id,
            "owner_id": owner_id,
            "owner_name": owner_name,
            "platform_name": platform_name,
            "src_platform_id": src_platform_id,
            "total_vm": len(total_vm_list),
            "migrated_vm": len(migrated_vm_list),
            "processing_vm": len(processing_vm_list)
        }
        task_set.append(task_data)

    total = tb_task_obj.get_count(user_id=user_id, search_word=search_word)
    datas = {"task_set": task_set, "total_count": total}
    return return_success(req, None, datas=datas)


def handle_detail_migration_task(req):
    """获取迁移任务详情"""
    logger.debug('handle detail migration task start, {}'.format(req))
    task_id = req.get("task_id")

    # 存在性检测
    task_info = tb_task_obj.query_migration_task(task_id)
    if not task_info:
        logger.error("migration task not exists, task id: {}".format(task_id))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS.value,
                                  ErrorMsg.ERR_MSG_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS.value))

    owner_id = task_info.get("owner_id")
    user_ret = ctx.iaas.desc_users(users=[owner_id])
    owner_info = None
    if user_ret and user_ret.get("ret_code") == 0 and user_ret.get("user_set"):
        user_set = user_ret.get("user_set")
        owner_info = user_set[0]

    task = {
        "task_id": task_info.get("task_id"),
        "task_name": task_info.get("task_name"),
        "task_desc": task_info.get("task_desc"),
        "task_pattern": task_info.get("task_pattern"),
        "create_time": task_info.get("record_create_time"),
        "dst_node_id": task_info.get("dst_node_id"),
        "dst_zone_id": task_info.get("dst_zone_id"),
        "dst_region_id": task_info.get("dst_region_id"),
        "src_datacenter_name": task_info.get("src_datacenter_name"),
        "src_platform_type": SrcPlatformType.VMWARE.value,
        "owner_id": task_info.get("owner_id"),
        "owner_name": owner_info["user_name"]
    }

    return return_success(req, None, datas=task)


def handle_describe_migration_vm(req):
    """获取迁移任务中的所有虚拟机的信息"""
    logger.debug('handle describe migration vm start, {}'.format(req))
    offset = req.get("offset")
    limit = req.get("limit")
    task_id = req.get("task_id")

    # 存在性检查
    task_info = tb_task_obj.query_migration_task(task_id)
    if not task_info:
        logger.error("migration task not exists, task id: {}".format(task_id))
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS.value,
                                  ErrorMsg.ERR_MSG_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS.value))

    vm_list = tb_vm_obj.list_vm(task_id=task_id, limit=limit,
                                offset=offset, sort_key="priority")
    if not vm_list:
        logger.error("included vm not exists, task id: {}".format(task_id))
        return return_error(req,
                            Error(
                                ErrorCode.ERR_CODE_MIGRATION_TASK_INCLUDED_VM_NOT_EXISTS.value,
                                ErrorMsg.ERR_MSG_MIGRATION_TASK_INCLUDED_VM_NOT_EXISTS.value))

    # 汇总查询vxnet信息
    vxnet_id_list = []
    for vm_info in vm_list:
        assert "dst_vm_net" in vm_info
        net_list = vm_info.get("dst_vm_net")
        assert isinstance(net_list, list)
        for net_info in net_list:
            vxnet_id = net_info.get("vxnet_id")
            if vxnet_id not in vxnet_id_list:
                vxnet_id_list.append(vxnet_id)
    vxnet_map = {}
    vxnet_ret = ctx.iaas.describe_vxnets(vxnets=vxnet_id_list)
    if vxnet_ret.get("ret_code") == 0 and vxnet_ret.get("vxnet_set"):
        vxnet_set = vxnet_ret.get("vxnet_set")
        for vxnet_data in vxnet_set:
            vxnet_map[vxnet_data["vxnet_id"]] = vxnet_data

    vm_session_list = []
    for vm_info in vm_list:
        vm_session = {
            "session_id": vm_info.get("session_id"),
            "src_vm_os_type": vm_info.get("src_vm_os_type"),
            "src_vm_name": vm_info.get("src_vm_name"),
            "src_vm_net": vm_info.get("src_vm_net"),
            "src_vm_disk": vm_info.get("src_vm_disk"),
            "src_vm_id": vm_info.get("src_vm_id"),
            "user_id": vm_info.get("user_id"),
            "process": vm_info.get("process"),
            "priority": vm_info.get("priority"),
            "status": vm_info.get("status"),
            "start_time": vm_info.get("start_time"),
            "end_time": vm_info.get("end_time"),
            "indeed_dst_node_id": vm_info.get("indeed_dst_node_id"),
            "indeed_dst_node_ip": vm_info.get("indeed_dst_node_ip"),
            "dst_vm_disk": vm_info.get("dst_vm_disk"),
            "dst_vm_os_disk": vm_info.get("dst_vm_os_disk"),
            "dst_vm_image": vm_info.get("dst_vm_image"),
            "dst_vm_name": vm_info.get("dst_vm_name"),
            "dst_vm_cpu_core": vm_info.get("dst_vm_cpu_core"),
            "dst_vm_memory": vm_info.get("dst_vm_memory"),
            "dst_vm_type": vm_info.get("dst_vm_type"),
            "dst_vm_os_type": vm_info.get("dst_vm_os_type"),
            "dst_vm_os_name": vm_info.get("dst_vm_os_name"),
            "dst_vm_id": vm_info.get("dst_vm_id"),
            "step": vm_info.get("step"),
            "err_code": vm_info.get("err_code"),
            "err_msg": vm_info.get("err_msg")
        }

        layout_dst_vm_net = []
        for net in vm_info.get("dst_vm_net"):
            vxnet_id = net.get("vxnet_id")
            vxnet_data = vxnet_map[vxnet_id]
            net_data = {
                "vxnet_id": vxnet_data.get("vxnet_id"),
                "vxnet_type": vxnet_data.get("vxnet_type"),
                "vxnet_name": vxnet_data.get("vxnet_name"),
                "vpc_router_id": vxnet_data.get("vpc_router_id"),
                "router": vxnet_data.get("router"),
                "ip": net.get("ip") or ""
            }
            layout_dst_vm_net.append(net_data)
        vm_session["dst_vm_net"] = layout_dst_vm_net

        # 处理部分虚拟机没有单独的数据盘
        if vm_info.get("dst_vm_data_disk"):
            vm_session["dst_vm_data_disk"] = vm_info.get("dst_vm_data_disk")

        vm_session_list.append(vm_session)

    return return_success(req, None, datas={"vms_config": vm_session_list,
                                            "total_count": len(vm_session_list)})


HANDLER_MAP = {
    ACTION_V2V_MIGRATION_TASK_CREATE_MIGRATION_TASK: handle_create_migration_task,
    ACTION_V2V_MIGRATION_TASK_UPDATE_MIGRATION_TASK: handle_update_migration_task,
    ACTION_V2V_MIGRATION_TASK_DELETE_MIGRATION_TASK: handle_delete_migration_task,
    ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_TASK: handle_describe_migration_task,
    ACTION_V2V_MIGRATION_TASK_DETAIL_MIGRATION_TASK: handle_detail_migration_task,
    ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_VM: handle_describe_migration_vm
}
