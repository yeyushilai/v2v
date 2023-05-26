# -*- coding: utf-8 -*-

from log.logger import logger
from utils.json import json_dump
from zk.dlock import dlock

from fg import context
from fg.dto.vm_session_dto import VmSession
from fg.uutils.pg.interface import (
    TableMigrateTask,
    TableVm
)
from fg.return_tools import (
    return_error,
    return_success
)
from fg.error import (
    Error,
    ErrorMsg,
    ErrorCode
)
from fg.constants import (
    # action
    ACTION_V2V_MIGRATION_VM_UPDATE_VM,
    ACTION_V2V_MIGRATION_VM_DELETE_VM,
    ACTION_V2V_MIGRATION_VM_OPERATE_VM,

    # migration
    MigrateStatus
)

CTX = context.instance()
tb_task_obj = TableMigrateTask()
tb_vm_obj = TableVm()


def handle_operate_migration_vm(req):
    """迁移任务中的虚拟机执行动作"""
    logger.debug('handle operate migration vm start, {}'.format(req))
    task_id = req.get("task_id")
    session_ids = req.get("session_ids")

    # 查询任务和虚拟机信息
    vm_list = tb_vm_obj.list_vm(task_id=task_id, session_id=session_ids)
    task = tb_task_obj.query_migration_task(task_id)

    # 调度任务到redis
    mg_key = "v2v_" + task.get("dst_node_id", "auto")
    task_flag = False
    with dlock(mg_key, CTX.zk, 2):
        task_ids = CTX.redis.lrange(mg_key, 0, -1)
        if task_ids is not None and (task_id not in task_ids):
            task_flag = CTX.redis.rpush(mg_key, task_id)
        if task_id in task_ids:
            task_flag = True
    if not task_flag:
        logger.error("scheduler task to redis error, task id: {task_id}, "
                     "session ids: {session_ids}"
                     "".format(task_id=task_id, session_ids=session_ids))
        return return_error(req,
                            Error(
                                ErrorCode.ERR_CODE_MIGRATION_TASK_SCHEDULER_MIGRATION_TASK_ERROE.value,
                                ErrorMsg.ERR_MSG_MIGRATION_TASK_SCHEDULER_MIGRATION_TASK_ERROE.value))

    # 更新迁移虚拟机状态和相关字段
    success_list = []
    failed_list = []
    for vm_info in vm_list:
        session_id = vm_info.get("session_id")
        origin_status = vm_info.get("status")
        if origin_status in MigrateStatus.list_schedulable_migrate_status():
            update_data = {"status": MigrateStatus.QUEUING.value}
        elif origin_status == MigrateStatus.FAILED.value:
            update_data = {
                "status": MigrateStatus.PENDING.value,
                "err_code": 0,
                "err_msg": "",
                "step": json_dump({}),
                "start_time": None,
                "end_time": None,
                "dst_vm_id": "",
                "dst_vm_create_time": None,
                "indeed_dst_node_id": "",
                "indeed_dst_node_ip": "",
                "process": 0
            }
        else:
            logger.error("the status of migration vm is invalid, status: "
                         "{status}, session id: {session_id}"
                         "".format(status=origin_status,
                                   session_id=session_id))
            continue

        logger.info("operate migration vm ready, session id: {session_id}, "
                    "update info: {update_data}"
                    "".format(session_id=session_id, update_data=update_data))
        aff_cnt = tb_vm_obj.update_vm(condition={"session_id": session_id},
                                      columns=update_data)
        if aff_cnt > 0:
            success_list.append(session_id)
        else:
            failed_list.append(session_id)
            logger.error("operate migration vm failed, session id: "
                         "{session_id}, update info: {update_data}"
                         "".format(session_id=session_id,
                                   update_data=update_data))

    logger.info("operate migration vm end, success list: {success_list}, "
                "failed list: {failed_list}"
                "".format(success_list=success_list, failed_list=failed_list))
    if len(session_ids) == len(success_list):
        return return_success(req, dict(data="ok"))
    else:
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_MIGRATION_VM_OPERATE_PART_MIGRATION_VM_ERROE.value,
                                  ErrorMsg.ERR_MSG_MIGRATION_VM_OPERATE_PART_MIGRATION_VM_ERROE.value,
                                  success_list=success_list,
                                  failed_list=failed_list))


def handle_delete_migration_vm(req):
    """删除迁移任务中的虚拟机"""
    logger.debug('handle delete migration vm start, {}'.format(req))
    session_ids = req.get("session_ids")
    user_id = req["sender"].get("user_id")
    task_id = req.get("task_id")

    vm_list = tb_vm_obj.list_vm(user_id=user_id, session_id=session_ids)

    success_list = []
    failed_list = []
    for vm_info in vm_list:
        session_id = vm_info["session_id"]
        if vm_info.get("status") in MigrateStatus.list_support_delete_status():
            vm_cnt = tb_vm_obj.update_vm(condition={"session_id": session_id},
                                         columns={"is_delete": True})

            if vm_cnt <= 0:
                failed_list.append(session_id)
            else:
                success_list.append(session_id)
        else:
            failed_list.append(session_id)

    logger.info("delete migration vm end, success list: {success_list}, "
                "failed list: {failed_list}"
                "".format(success_list=success_list, failed_list=failed_list))

    # 所有虚拟机被删空，则删除迁移任务
    task_vm_list = tb_vm_obj.list_vm(user_id=user_id, task_id=task_id)
    if not task_vm_list:
        task_cnt = tb_task_obj.update_migration_task(condition={"task_id": task_id},
                                                     columns={"is_delete": True})
        if task_cnt <= 0:
            logger.error("the inclueded vm of task has deleted, try to delete"
                         " migration task but failed, task id: {}"
                         "".format(task_id))
            return return_error(req,
                                Error(
                                    ErrorCode.ERR_CODE_MIGRATION_VM_DELETE_RELATIVE_MIGRATION_TASK_ERROE.value,
                                    ErrorMsg.ERR_MSG_MIGRATION_VM_DELETE_RELATIVE_MIGRATION_TASK_ERROE.value))

    # 汇总结果
    if len(session_ids) == len(success_list):
        return return_success(req, dict(data="ok"))
    else:
        return return_error(req,
                            Error(ErrorCode.ERR_CODE_MIGRATION_VM_DELETE_PART_MIGRATION_VM_ERROE.value,
                                  ErrorMsg.ERR_MSG_MIGRATION_VM_DELETE_PART_MIGRATION_VM_ERROE.value,
                                  success_list=success_list,
                                  failed_list=failed_list))


def handle_update_migration_vm(req):
    """更新迁移任务中的虚拟机"""
    logger.debug('handle update migration vm start, {}'.format(req))
    vm_config = req.get("vm_config")
    session_id = req.get("session_id")
    task_id = req.get("task_id")
    vm_config["task_id"] = task_id

    vm_session = VmSession(session_id=session_id)
    aff_cnt = vm_session.update_config_to_pg(vm_config)
    if aff_cnt < 0:
        logger.error("update migration vm failed, session id: {session_id}, vm"
                     " config: {vm_config}"
                     "".format(session_id=session_id,
                               vm_config=vm_session.config))
        return return_error(req,
                            Error(
                                ErrorCode.ERR_CODE_MIGRATION_VM_UPDATE_MIGRATION_VM_ERROR.value,
                                ErrorMsg.ERR_MSG_MIGRATION_VM_UPDATE_MIGRATION_VM_ERROR.value))
    return return_success(req, None, datas=vm_session.config)


HANDLER_MAP = {
    ACTION_V2V_MIGRATION_VM_OPERATE_VM: handle_operate_migration_vm,
    ACTION_V2V_MIGRATION_VM_DELETE_VM: handle_delete_migration_vm,
    ACTION_V2V_MIGRATION_VM_UPDATE_VM: handle_update_migration_vm
}
