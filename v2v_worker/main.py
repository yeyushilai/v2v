#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

# 设置日志名称
from log.logger_name import set_logger_name
set_logger_name("v2v_worker")
from log.logger import logger

from utils.misc import get_current_time
from api.constants import HYPERNODE_STATUS_ACTIVE

from worker import Worker
from context import WorkerContext
from dispatcher import dispatch_task, dispatch_vm


from constants.common import (
    # 当前节点信息
    LOCAL_NODE_ID,

    # 自身
    MAX_MIGRATING_NUM,
    DATA_DIR,

    # 调试
    CONCURRENCY_MIGRATE,

    # 迁移全局
    INDEED_START_MIGRATE_TIMEOUT,
    INDEED_END_MIGRATE_TIMEOUT,

    # 导出镜像
    EXPORT_IMAGE_DST_BASE_DIR,
    EXPORT_IMAGE_LOG_PATH,

    # 上传镜像
    UPLOAD_IMAGE_DST_BASE_DIR,

    # 转换镜像
    # DEAL_IMAGE_MOUNT_BASE_DIR,
    # DEAL_IMAGE_FILE_LOCK_BASE_DIR,

    # 迁移相关
    MigrateStatus,
    WorkerAction
)
from constants.error import ErrorCode, ErrorMsg

# 初始化上下文
ctx = WorkerContext()
CTX = ctx


def check_hyper_node():
    bot_set = CTX.iaas.describe_bots(hyper_ids=[LOCAL_NODE_ID],
                                     zone=CTX.local_node.zone_id)
    hyper_status = bot_set.get("status")
    if hyper_status != HYPERNODE_STATUS_ACTIVE:
        err_msg = "the status of hyper node is invalid, node id: {node_id}, " \
                  "status: {status}" \
                  "".format(node_id=LOCAL_NODE_ID, status=hyper_status)
        logger.error(err_msg)
        raise Exception(err_msg)


def init_directory():
    """初始化目录"""

    # V2V项目的基准目录
    # eg: /pitrix/data/v2v
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)

    # 导出镜像时，若相关的日志所在的目录未生成，需要生成
    export_image_log_base_dir = os.path.dirname(EXPORT_IMAGE_LOG_PATH)
    if not os.path.isdir(export_image_log_base_dir):
        os.mkdir(export_image_log_base_dir)

    # 导出镜像时，临时保存镜像的基准目录
    # eg: /pitrix/data/v2v/v2v_export
    if not os.path.isdir(EXPORT_IMAGE_DST_BASE_DIR):
        os.mkdir(EXPORT_IMAGE_DST_BASE_DIR)

    # 上传镜像时，临时保存镜像的基准目录
    # eg: /pitrix/data/v2v/v2v_upload
    if not os.path.isdir(UPLOAD_IMAGE_DST_BASE_DIR):
        os.mkdir(UPLOAD_IMAGE_DST_BASE_DIR)


def register_hyper_node():
    """注册zk"""

    # 从zk中删除节点
    CTX.zk.delete_hyper_node(LOCAL_NODE_ID)

    # 注册节点到zk
    CTX.zk.register_hyper_node(LOCAL_NODE_ID)

    # 去zk检查是否注册成功
    CTX.zk.check_hyper_node(LOCAL_NODE_ID)


def reset_remained_vms():
    """重置之前残余的关联虚拟机"""
    # 如果识别到当前hyper节点关联的虚拟机为运行状态，则直接强制改为失败状态
    vms = CTX.v2v_pg.list_vm(hyper_node_id=LOCAL_NODE_ID,
                             status=MigrateStatus.RUNNING.value)

    # 取空判断
    if not vms:
        logger.info("remained vms not exists")
        return

    session_id_list = list()
    err_code = ErrorCode.ERROR_WORKER_SERVICE_RESET.value
    err_msg = ErrorMsg.ERROR_WORKER_SERVICE_RESET.value
    for vm_session in vms:
        session_id = vm_session["session_id"]
        status = MigrateStatus.FAILED.value
        end_time = get_current_time()
        detail_status = dict(status=status, end_time=end_time,
                             err_code=err_code, err_msg=err_msg.zh)
        CTX.v2v_pg.update_vm(session_id=session_id, columns=detail_status)
        session_id_list.append(session_id)

        logger.info("reset vm session to failed successfully, session id: "
                    "{session_id}, err code: {err_code}, err msg: {err_msg}"
                    "".format(session_id=session_id,
                              err_msg=err_msg.en,
                              err_code=err_code))

    logger.info("reset remained vms to failed status end, session_id_list: %s"
                % session_id_list)


def supervise_worker(v2v_worker):
    """监管worker状态"""

    for thread, worker in v2v_worker.thread_worker_mapper.items():
        # 过滤掉死亡的线程
        if not thread.is_alive():
            continue

        # 过滤动作
        if worker["action"] != WorkerAction.IMMEDIATELY_MIGRATE.value:
            continue

        # 过滤不存在的虚拟机
        vm_session = worker["params"]
        session_id = vm_session["session_id"]
        vm_db_info = CTX.v2v_pg.query_vm(session_id)
        if not vm_db_info:
            continue

        # 过滤状态不合适的虚拟机
        if vm_db_info["status"] != MigrateStatus.RUNNING.value:
            continue

        logger.info("vm is migrating, session id: {session_id}, step: {step}, "
                    "thread name: {thread_name}, thread id: {thread_id}"
                    "".format(thread_name=thread.name,
                              thread_id=thread.ident,
                              session_id=session_id,
                              step=vm_db_info["step"]["step"]))

        # 存活线程的处置方法
        current_time = get_current_time()
        err_code = ErrorCode.SUCCESS.value
        err_msg = ErrorMsg.SUCCESS.value

        vm_db_step = vm_db_info["step"]["step"]
        vm_db_start_time = vm_db_info["start_time"]
        total_seconds = int((current_time - vm_db_start_time).total_seconds())

        # 存活线程对应的迁移主机，若迟迟不执行动作，直接重置状态为失败
        if total_seconds > INDEED_START_MIGRATE_TIMEOUT and not vm_db_step:
            err_code = ErrorCode.ERROR_DISPATCH_START_MIGRATE_TIMEOUT.value
            err_msg = ErrorMsg.ERROR_DISPATCH_START_MIGRATE_TIMEOUT.value

        # 存活线程对应的迁移主机，若超时未完成迁移，直接重置状态为失败
        elif total_seconds > INDEED_END_MIGRATE_TIMEOUT:
            err_code = ErrorCode.ERROR_DISPATCH_END_MIGRATE_TIMEOUT.value
            err_msg = ErrorMsg.ERROR_DISPATCH_END_MIGRATE_TIMEOUT.value
        else:
            pass

        if err_code == ErrorCode.SUCCESS.value:
            continue

        status = MigrateStatus.FAILED.value
        detail_status = dict(status=status, end_time=current_time,
                             err_code=err_code, err_msg=err_msg.zh)
        CTX.v2v_pg.update_vm(session_id=session_id, columns=detail_status)
        logger.error("reset vm session to failed successfully, session id: "
                     "{session_id} , step: {step}, err code: {err_code}, error"
                     " reason: {err_msg}, thread name: {thread_name}, thread id"
                     ": {thread_id}"
                     .format(session_id=session_id,
                             step=vm_db_step,
                             err_msg=err_msg.en,
                             err_code=err_code,
                             thread_name=thread.name,
                             thread_id=thread.ident))


def check_local_node_queue():
    """判断当前节点是否有空闲的队列
    有空闲队列，可以继续调度一个主机发起迁移的话，返回True
    超过或者已经达到上限值，则抛出异常
    """

    # 判断依据:从pg中提取记录判断，当前正在迁移的主机，事实上的目标hyper节点为本机
    vms = CTX.v2v_pg.list_vm(hyper_node_id=LOCAL_NODE_ID,
                             status=MigrateStatus.RUNNING.value)

    if len(vms) > MAX_MIGRATING_NUM:
        log_msg = "local node({node_id}) now execute {num} migration, " \
                  "has out of range" \
                  "".format(node_id=LOCAL_NODE_ID,
                            num=MAX_MIGRATING_NUM)
        logger.error(log_msg)
        raise Exception(log_msg)
    return True


def loop():
    """循环调度任务，调度待迁移主机、执行迁移"""
    action = WorkerAction.IMMEDIATELY_MIGRATE.value
    v2v_worker = Worker(CONCURRENCY_MIGRATE)

    while True:
        try:
            # 监管当前worker的状态
            supervise_worker(v2v_worker)

            # 判断当前节点是否有空闲的队列
            check_local_node_queue()

            # 调度一个迁移任务
            task_info = dispatch_task()
            if not task_info:
                logger.info("dispatch a suitable task failed, sleep 30s")
                time.sleep(30)
                continue

            # 从迁移任务中调度出一个待迁移的虚拟机
            vm_session = dispatch_vm(task_info)
            if not vm_session:
                logger.info("dispatch a suitable vm failed, task id: {task_id}"
                            ", sleep 30s"
                            "".format(task_id=task_info["task_id"]))
                time.sleep(30)
                continue

            # 执行迁移动作
            v2v_worker.start(action, vm_session)
            logger.info("dispatch a suitable vm and send migrate request "
                        "successfully, session id: {session_id}, "
                        "task id: {task_id}"
                        "".format(session_id=vm_session["session_id"],
                                  task_id=task_info["task_id"]))

        except Exception as e:
            log_msg = "dispatch a suitable vm and send migrate request failed," \
                      " sleep 30s, error reason: {reason}" \
                      "".format(reason=str(e))
            logger.exception(log_msg)
            time.sleep(30)

        finally:
            logger.info("sleep 5s")
            time.sleep(5)


def main():

    # 初始化目录
    init_directory()

    # 自检hyper节点
    check_hyper_node()

    # 注册hyper节点
    register_hyper_node()

    # 重置残留的关联虚拟机
    reset_remained_vms()

    # 循环调度任务，调度待迁移主机、执行迁移
    loop()


if __name__ == '__main__':
    main()
