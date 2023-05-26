# -*- coding: utf-8 -*-

import time

from log.logger import logger

from context import WorkerContext
from constants.pg import JobTableStatus

CTX = WorkerContext()


def wait_job_successful(job_id, timeout=60 * 10):
    """
    等待JOB执行完毕
    :param job_id: JOB ID
    :param timeout: 超时时间
    :return: 超时时间内完成返回True，否则抛出异常
    """
    src_timeout = timeout
    while True:
        status_dict = CTX.zone_pg.query_job(job_id)

        # 过滤未知状态
        if not status_dict or "status" not in status_dict.keys():
            log_msg = 'query job status failed, status not found, job id: ' \
                      '{job_id}'.format(job_id=job_id)
            logger.error(log_msg)
            raise Exception(log_msg)

        status = status_dict["status"]
        action = status_dict["job_action"]
        error_codes = status_dict["error_codes"]

        # 过滤失败的终态
        if status in [JobTableStatus.FAILED.value,
                      JobTableStatus.DONE_WITH_FAILURE.value]:
            log_msg = 'job execute failed, job id: {job_id}, action: {action},' \
                      ' status: {status}, error_codes: {error_codes}'\
                .format(job_id=job_id, status=status,
                        action=action, error_codes=error_codes)
            logger.error(log_msg)
            raise Exception(log_msg)

        # 执行成功，则直接跳出循环
        if status == JobTableStatus.SUCCESSFUL.value:
            logger.info("job execute successfully, job id: {job_id}, action: "
                        "{action}, status: successful"
                        .format(job_id=job_id, status=status, action=action))
            return bool(status)

        if timeout <= 0:
            log_msg = 'wait job execute to success timeout, job id: {job_id}, ' \
                      'action: {action}, status: {status}, timeout: {timeout}, ' \
                      'src timeout: {src_timeout}' \
                      ''.format(job_id=job_id, status=status,
                                action=action, timeout=timeout,
                                src_timeout=src_timeout)
            logger.error(log_msg)
            raise Exception(log_msg)
        else:
            logger.info("wait job execute to success, job id: {job_id}, action"
                        ": {action}, status: {status}, timeout: {timeout}, now"
                        " will sleep 3s"
                        .format(job_id=job_id, action=action,
                                status=status, timeout=timeout))
            time.sleep(3)
            timeout -= 3
