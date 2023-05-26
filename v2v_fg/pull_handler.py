# -*- coding: utf-8 -*-

"""
Created on 2013-02-22

@author: yunify
"""
import time
from utils.json import json_load
from log.logger import logger
from api.error import Error
from api.error_code import INTERNAL_ERROR
from api.constants import JOB_STATUS_FAIL
from utils.misc import get_current_time

from fg.leasing import update_resource_leasing
from fg import context
from fg.constants import (
    TB_JOB,
    TASK_ACTION_UPDATE_RESOURCE_LEASING,
)


def handle_task_update_resource_leasing(req):
    """ init global environment for user """
    required_params = ["resource"]
    for param in required_params:
        if param not in req or not req[param]:
            logger.error("missing parameter [%s] in this request [%s]"
                         % (param, req))
            return -1
    resource_id = req['resource']
    extra = req.get('extra')

    # send request and retry
    cnt = 0
    retry = 18
    interval = 10
    while cnt < retry:
        ret = update_resource_leasing(resource_id, extra)
        if not isinstance(ret, Error) or\
                (isinstance(ret, Error) and
                 ret.get_code() != INTERNAL_ERROR):
            return 0
        time.sleep(interval)
        cnt += 1
        logger.warn("update resource [%s] leasing failed, "
                    "retry for the [%s] time" % (resource_id, cnt))
        continue

    logger.critical("update resource [%s] leasing failed after retry for "
                    "[%s] times" % (resource_id, cnt))
    return -1


class PullServiceHandler(object):
    """ long time service handler
    """

    def __init__(self):
        self.handler = {
            TASK_ACTION_UPDATE_RESOURCE_LEASING:
                handle_task_update_resource_leasing,
        }

    def handle(self, req_msg, title, **kargs):
        """ no return"""

        # decode to request object
        req = json_load(req_msg)
        if req is None:
            logger.error("invalid request: %s" % req_msg)
            return

        if "req_type" not in req:
            logger.error("invalid request: %s" % req_msg)
            return

        req_type = req["req_type"]
        if req_type not in self.handler:
            logger.error("can not handle this type [%s]" % req_type)
            return
        if 0 != self.handler[req_type](req):
            logger.error("handle request [%s] failed" % req)
            
            # update job failed
            if "job_id" in req and req['job_id']:
                ctx = context.instance()
                ctx.zone_pg.update(TB_JOB, req['job_id'], {'status': JOB_STATUS_FAIL, 'status_time': get_current_time()})
            return
        logger.info("handle request [%s] OK" % req)
        return
