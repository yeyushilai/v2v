# -*- coding: utf-8 -*-

import os

# 设置日志名称
from log.logger import logger

from utils.misc import get_current_time
from api.constants import HYPERNODE_STATUS_ACTIVE
from zk.dlock import dlock


from context import WorkerContext


from constants.zk import (
    DLOCK_KEY,
    DLOCK_TIMEOUT
)

# pitrix上面的虚拟机
from constants.iaas import (
    # # 虚拟机
    # SupportInstanceType,


    # 磁盘
    SupportVolumeType,
)

from constants.common import (
    # 当前节点信息
    LOCAL_NODE_ID,
    LOCAL_NODE_IP,

    # 导出镜像
    EXPORT_IMAGE_DST_BASE_DIR,

    # 上传镜像
    UPLOAD_IMAGE_DST_BASE_DIR,

    # 转换镜像
    # DEAL_IMAGE_MOUNT_BASE_DIR,

    # 迁移相关
    MigrateStatus,
    MigratePattern
)
from constants.error import ErrorCode, ErrorMsg


from uutils.common import normal_exec


# 初始化上下文
CTX = WorkerContext()

# 迁移模式映射
MIGRATE_PATTERN_MAPPER = {
    1: MigratePattern.EXPORT_IMAGE.value,
    2: MigratePattern.UPLOAD_IMAGE.value
}


# 本节点不支持调度的迁移任务（黑名单）
dispatch_task_black_list = list()

# 本节点不支持创建的虚拟机类型的会话列表
unsupported_instance_type_vm_list = list()

# 本节点不支持创建的虚拟机硬盘类型的会话列表
unsupported_volume_type_vm_list = list()

# 非法的虚拟机硬盘类型的会话列表
invalid_volume_type_vm_list = list()


def get_wait_migrate_vm_in_task(task_id):
    """获取迁移任务中等待迁移的虚拟机列表"""
    wait_migrate_status_list = MigrateStatus.list_wait_migrate_status()
    return CTX.v2v_pg.list_vm(task_id=task_id,
                              status=wait_migrate_status_list,
                              sort_key="priority")


def dispatch_task():
    """调度一个迁移任务"""
    local_node = CTX.local_node
    define_node_task_list = CTX.redis.get_define_node_task(local_node.node_id)
    auto_node_task_list = CTX.redis.get_auto_node_task()
    task_list = define_node_task_list + auto_node_task_list

    # 取空检查
    if not task_list:
        logger.info("there is not waiting migrate task")
        return
    logger.info("waiting migrate task list(from redis): %s" % task_list)

    global dispatch_task_black_list
    logger.info("dispatch task black list: {dispatch_task_black_list}"
                "".format(dispatch_task_black_list=dispatch_task_black_list))

    tasks = {task_info["task_id"]: task_info for task_info in
             CTX.v2v_pg.list_migrate_task()}

    for task_id in task_list:
        if task_id not in tasks.keys():
            logger.info("task id(from redis) is not in task list(from pg), "
                        "continue, task id: %s" % task_id)
            continue

        # 黑名单过滤
        if task_id in dispatch_task_black_list:
            logger.info("task id in dispatch task black list, continue, "
                        "task id: {task_id}".format(task_id=task_id))
            continue

        task_info = tasks[task_id]
        # hyper节点适配性检查
        if task_info["dst_node_id"] not in [local_node.node_id, "auto"]:
            # 如果任务指定了hyper节点且非本地hyper节点，则直接跳过
            logger.info(
                "migrate task is not suitable, task({task_id})'s dst node id is "
                "{dst_node_id}, hyper node's node id is {hyper_node_id}"
                .format(task_id=task_id,
                        dst_node_id=task_info["dst_node_id"],
                        hyper_node_id=local_node.node_id))
            continue

        # 可用区适配性检查
        if local_node.zone_id != task_info["dst_zone_id"]:
            logger.info("migrate task is not suitable, task({task_id})'s zone "
                        "id is {task_zone_id}, hyper node({node_id})'s zone id"
                        " is {node_zone_id}"
                        .format(task_id=task_id,
                                task_zone_id=task_info["dst_zone_id"],
                                node_id=local_node.node_id,
                                node_zone_id=local_node.zone_id))
            continue

        logger.info("dispatch a suitable task successfully, task id: "
                    "{task_id}".format(task_id=task_id))
        return task_info
    else:
        logger.info("dispatch a suitable task failed")


def dispatch_vm(task_info):
    with dlock(DLOCK_KEY, CTX.zk.zk_client, DLOCK_TIMEOUT):
        
        # 从迁移任务中调度出一个待迁移的虚拟机
        vm_session = dispatch_vm_from_task(task_info)

        if vm_session:
            # 判断当前hyper节点是否有空闲的硬件资源
            if not check_local_node_resource(vm_session):
                logger.info("check local node resource failed, node id: "
                            "{node_id}, session id: {session_id}"
                            "".format(node_id=LOCAL_NODE_ID,
                                      session_id=vm_session["session_id"]))
                return

            # 初始化迁移虚拟机的相关信息
            vm_session = init_vm_session(task_info, vm_session)

        # 更新redis中节点对应的任务
        update_relative_queue_task(task_info)

        return vm_session


def dispatch_vm_from_task(task_info):
    """从迁移任务中调度出一个待迁移的虚拟机
    参数task_info要求：
    1.任务指定本节点运行或者自动节点运行
    2.任务的可用区与本节点一致
    """
    task_id = task_info["task_id"]
    vm_info_list = get_wait_migrate_vm_in_task(task_id)

    # 取空检查
    if not vm_info_list:
        logger.info("there is not wait migrate vm in task, task id: "
                    "{task_id}".format(task_id=task_id))
        return

    # 合法性检查
    global unsupported_instance_type_vm_list
    global unsupported_volume_type_vm_list
    global invalid_volume_type_vm_list
    global dispatch_task_black_list
    unsupported_instance_type_vm_list = list()
    unsupported_volume_type_vm_list = list()
    invalid_volume_type_vm_list = list()

    support_resource = CTX.local_node.query_support_resource()
    for vm_info in vm_info_list:
        dispatch_tag = True  # True代表合法， False代表不合法
        session_id = vm_info["session_id"]

        # 检查当前的hyper节点支持的云服务器类型是否匹配宿虚拟机类型，若不支持则统计
        if vm_info["dst_vm_type"] not in support_resource["instance_type"]:
            unsupported_instance_type_vm_list.append(session_id)
            dispatch_tag = False

        # TODO:增加支持的虚拟机类型检测
        volume_types = [vm_info["dst_vm_os_disk"]["type"]]
        if "dst_vm_data_disk" in vm_info \
                and isinstance(vm_info["dst_vm_data_disk"], dict) \
                and "type" in vm_info["dst_vm_data_disk"]:
            volume_types.append(vm_info["dst_vm_data_disk"]["type"])
        for volume_type in volume_types:
            # 检查宿虚拟机硬盘类型，是否被迁移服务支持，若不支持则统计
            if volume_type not in SupportVolumeType.list_type():
                invalid_volume_type_vm_list.append(session_id)
                dispatch_tag = False
                break

            # 检查当前的hyper节点支持的硬盘类型是否匹配宿虚拟机硬盘类型，若不支持则统计
            if volume_type not in support_resource["volume_type"]:
                unsupported_volume_type_vm_list.append(session_id)
                dispatch_tag = False
                break

        if not dispatch_tag:
            continue

        # 全部检查通过，已经挑选出来了合适的待迁移主机
        logger.info("dispatch a suitable vm successfully, session id: "
                    "{session_id}, src status: {src_status}, task id: {task_id}"
                    .format(task_id=task_id,
                            src_status=vm_info["status"],
                            session_id=session_id))
        return vm_info
    else:
        logger.info("dispatch a suitable vm failed, task id: {task_id}, "
                    "maybe reason follow:".format(task_id=task_id))
        if unsupported_instance_type_vm_list:
            logger.info("unsupported instance type exists, relative vm list: %s"
                        % unsupported_instance_type_vm_list)
        if unsupported_volume_type_vm_list:
            logger.info("unsupported volume type exists, relative vm list: %s"
                        % unsupported_volume_type_vm_list)
        if invalid_volume_type_vm_list:
            logger.info("invalid volume type exists, relative vm list: %s"
                        % invalid_volume_type_vm_list)

        # 走到这里，说明迁移任务中已经没有了能够迁移的虚拟机，直接将迁移任务拉入黑名单
        dispatch_task_black_list.append(task_id)

        # 若任务包含不合法的资源且指定本节点运行，为了避免后续重复取到，重置该任务中的虚拟机
        if task_info["dst_node_id"] == CTX.local_node.node_id:
            reset_unsupported_instance_type_vms()
            reset_unsupported_volume_type_vms(unsupported_volume_type_vm_list)

        # 若任务中存在非法的虚拟机配置，为了避免后续重复取到，重置该任务中的虚拟机
        if invalid_volume_type_vm_list:
            reset_unsupported_volume_type_vms(invalid_volume_type_vm_list)


def reset_unsupported_instance_type_vms():
    """重置不支持虚拟机类型的迁移项"""
    detail_status = dict(status=MigrateStatus.FAILED.value,
                         end_time=get_current_time())

    err_code = ErrorCode.ERROR_DST_VM_TYPE_INVALID.value
    err_msg = ErrorMsg.ERROR_DST_VM_TYPE_INVALID.value
    detail_status["err_msg"] = err_msg.zh
    detail_status["err_code"] = err_code
    for session_id in unsupported_instance_type_vm_list:
        CTX.v2v_pg.update_vm(session_id=session_id, columns=detail_status)
        logger.info("reset vm session to failed successfully, session id: "
                    "{session_id}, err code: {err_code}, err msg: {err_msg}"
                    "".format(session_id=session_id,
                              err_msg=err_msg.en,
                              err_code=err_code))


def reset_unsupported_volume_type_vms(vm_list):
    """重置不支持硬盘类型的迁移项"""
    detail_status = dict(status=MigrateStatus.FAILED.value,
                         end_time=get_current_time())

    err_code = ErrorCode.ERROR_DST_VM_VOLUME_TYPE_INVALID.value
    err_msg = ErrorMsg.ERROR_DST_VM_VOLUME_TYPE_INVALID.value
    detail_status["err_msg"] = err_msg.zh
    detail_status["err_code"] = err_code
    for session_id in vm_list:
        CTX.v2v_pg.update_vm(session_id=session_id, columns=detail_status)
        logger.info("reset vm session to failed successfully, session id: "
                    "{session_id}, err code: {err_code}, err msg: {err_msg}"
                    "".format(session_id=session_id,
                              err_msg=err_msg.en,
                              err_code=err_code))


def check_local_node_resource(vm_session):
    """判断当前节点是否有空闲的硬件资源"""

    bot_set = CTX.iaas.describe_bots(hyper_ids=[LOCAL_NODE_ID],
                                     zone=CTX.local_node.zone_id)
    session_id = vm_session["session_id"]

    # 检查状态
    hyper_status = bot_set.get("status")
    if hyper_status != HYPERNODE_STATUS_ACTIVE:
        err_msg = "the status of hyper node is invalid, node id: {node_id}, " \
                  "status: {status}" \
                  "".format(node_id=LOCAL_NODE_ID, status=hyper_status)
        logger.error(err_msg)
        return False

    # 检查CPU
    dst_vm_cpu_core = vm_session["dst_vm_cpu_core"]
    free_cpu_core = bot_set["free_vcpu"]
    if dst_vm_cpu_core > free_cpu_core:
        log_msg = "cpu core out of limit, session id: {session_id}, " \
                  "dst vm cpu core: {dst_vm_cpu_core}, " \
                  "free cpu core: {free_cpu_core}" \
                  "".format(session_id=session_id,
                            dst_vm_cpu_core=dst_vm_cpu_core,
                            free_cpu_core=free_cpu_core)
        logger.info(log_msg)
        return False

    # 检查内存
    dst_vm_memory = vm_session["dst_vm_memory"]
    free_memory = bot_set["free_memory"]
    if dst_vm_memory / 1024 > free_memory:
        log_msg = "memory out of limit, session id: {session_id}, " \
                  "dst vm memory: {dst_vm_memory}, " \
                  "free memory: {free_memory}" \
                  "".format(session_id=session_id,
                            dst_vm_memory=dst_vm_memory / 1024,
                            free_memory=free_memory)
        logger.info(log_msg)
        return False

    # 检查磁盘
    dst_vm_disk = vm_session["dst_vm_disk"]
    free_disk = bot_set.get("free_disk")
    vm_disk_size = 0
    for disk in dst_vm_disk:
        vm_disk_size += disk.get("size")
    if vm_disk_size > free_disk:
        log_msg = "disk size out of limit, session id: {session_id}, " \
                  "vm disk size: {vm_disk_size}, " \
                  "free disk: {free_disk}" \
                  "".format(session_id=session_id,
                            vm_disk_size=vm_disk_size,
                            free_disk=free_disk)
        logger.info(log_msg)
        return False

    return True


def init_vm_session(task_info, vm_session):
    """初始化迁移虚拟机的
    1.初始化目录
    2.更新相关信息到内存和v2v数据库
    """
    session_id = vm_session["session_id"]

    # 1.初始化目录
    logger.info("init directory, session id: {session_id}"
                "".format(session_id=session_id))
    vm_session["extra"] = dict()
    task_pattern = MIGRATE_PATTERN_MAPPER[task_info["task_pattern"]]
    if task_pattern == MigratePattern.EXPORT_IMAGE.value:
        export_dir = os.path.join(EXPORT_IMAGE_DST_BASE_DIR, session_id)
        if not os.path.isdir(export_dir):
            normal_exec("mkdir -p %s" % export_dir)
        vm_session["extra"]["export_dir"] = export_dir

    elif task_pattern == MigratePattern.UPLOAD_IMAGE.value:
        upload_dir = os.path.join(UPLOAD_IMAGE_DST_BASE_DIR, session_id)
        if not os.path.isdir(upload_dir):
            normal_exec("mkdir -p %s" % upload_dir)
        vm_session["extra"]["upload_dir"] = upload_dir

    # 2.更新相关信息到内存和v2v数据库
    running = MigrateStatus.RUNNING.value
    current_time = get_current_time()
    columns = dict(status=running,
                   indeed_dst_node_id=LOCAL_NODE_ID,
                   indeed_dst_node_ip=LOCAL_NODE_IP,
                   start_time=current_time)
    logger.info("init vm session, session id: {session_id}, src "
                "status: {src_status}, dst status: {dst_status}, "
                "start time: {start_time}"
                .format(session_id=session_id, src_status=vm_session["status"],
                        dst_status=running, start_time=current_time))
    vm_session.update(columns)
    CTX.v2v_pg.update_vm(session_id=session_id, columns=columns)

    return vm_session


def update_relative_queue_task(task_info):
    """更新redis中队列中对应的任务
    判断逻辑：若任务中的没有待迁移的虚拟机，则将任务ID从redis的数据结构中移除
    """
    task_id = task_info["task_id"]
    vm_list = get_wait_migrate_vm_in_task(task_id)
    if vm_list:
        return

    CTX.redis.remove_define_node_define_task(LOCAL_NODE_ID, task_id)
    CTX.redis.remove_auto_node_define_task(task_id)
    logger.info("there is not wait migrate vm in task, has removed "
                "task id from redis, task id: {task_id}"
                .format(task_id=task_id))
