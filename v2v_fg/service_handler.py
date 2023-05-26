# -*- coding: utf-8 -*-

import time
import logging
from functools import wraps

from log.logger import logger

from constants import LONG_HANDLE_TIME
from api.return_tools import return_error
from api.constants import REQ_EXPIRED_INTERVAL
from api.error import Error
from api.error_code import (
    INTERNAL_ERROR,
    INVALID_REQUEST_FORMAT
)
from api.error_msg import (
    ERR_MSG_ILLEGAL_REQUEST,
    ERR_MSG_VALIDATE_REQUEST_FAILED,
    ERR_MSG_MISSING_PARAMETER,
    ERR_MSG_CAN_NOT_HANDLE_REQUEST
)
from utils.json import json_load, json_dump
from utils.time_stamp import get_ts, get_expired_ts, cmp_ts, parse_ts
from server.shutdown.helper import handle_sync_message

from fg.constants import ACTION_REDIRECT_TO_WS
from fg.uutils import utils_common
from fg.handlers import (
    health_handler,
    iaas_handler,
    migration_task_handler,
    migration_vm_handler,
    nas_handler,
    src_platform_handler
)


gray = logging.getLogger("graylog")


def graylog(func):
    @wraps(func)
    def decor_warp(*args, **kwargs):
        req_msg = args[1]
        req = json_load(req_msg)
        action = req.get("action")
        start_time = time.time()
        rep = func(*args, **kwargs)
        end_time = time.time()
        rsp = json_load(rep)
        req_id = req.get("req_id")
        if not req_id:
            req_id = utils_common.generate_id()
        ret_code = rsp.get("ret_code")
        rsp["req_id"] = req_id
        gelf_props = {
                    "action": action,
                    "req": req,
                    "req_id": req_id,
                    "rep": rep,
                    "cost": end_time - start_time
                }
        if ret_code != 0:
            gray.error("ServiceHandler._handle log", extra={
                "gelf_props": gelf_props,
            })
        else:
            gray.info("ServiceHandler._handle log", extra={
                "gelf_props": gelf_props,
            })
        return json_dump(rsp)
    return decor_warp


class ServiceHandler(object):
    """ front gate - service handler """

    def __init__(self):
        # update handler map
        self.handle_map = dict()
        for handler in [
            health_handler,
            iaas_handler,
            migration_task_handler,
            migration_vm_handler,
            nas_handler,
            src_platform_handler
        ]:
            self.handle_map.update(handler.HANDLER_MAP)

    @staticmethod
    def _check_params(req):
        """ check required params """
        required_params = ["action", "sender"]
        for param in required_params:
            if param not in req:
                logger.error(
                    "[%s] not found in this request [%s]" % (param, req))
                return False

        # check sender format
        sender = req["sender"]
        if not isinstance(sender, dict):
            logger.error("illeage sender format [%s]" % sender)
            return False
        required_params = ["user_id", "privilege"]
        for param in required_params:
            if param not in sender:
                logger.error("[%s] not found in sender [%s]" % (param, sender))
                return False

        # either "expires" or "time_stamp" should be contained in params
        if "expires" not in req and "time_stamp" not in req:
            logger.error("[expires] and [time_stamp] both not found in "
                         "request [%s]" % req)
            return False

        # check time stamp format
        for param in ["expires", "time_stamp"]:
            if param not in req:
                continue
            if 0 == parse_ts(req[param]):
                logger.error("[%s]'s format is incorrect in request [%s]"
                             % (param, req))
                return False

        return True

    @staticmethod
    def _check_expires(req):
        """ check expires of request """
        current_time = get_ts()
        expires = req.get("expires", None)
        if expires is None:
            expires = get_expired_ts(req['time_stamp'], REQ_EXPIRED_INTERVAL)
        # request is expires if current_time greater than expires
        if 1 == cmp_ts(current_time, expires):
            logger.error(
                "request [%s] is expired, current_time [%s], expires [%s]" %
                (req, current_time, expires))
            return False
        return True

    @staticmethod
    def _validate(req):
        """ validate request """
        if not ServiceHandler._check_params(req):
            return -1
        if not ServiceHandler._check_expires(req):
            return -2

        return 0

    @staticmethod
    def _serialize(req):
        """ serialize request """
        rtype = req.get('sender', {}).get('channel', '')
        action = req.get('action', '')
        if action == ACTION_REDIRECT_TO_WS:
            action += ':%s' % req['ws_request']['action']
        identity = req.get('sender', {}).get('user_id', '')
        return ('type:(%s) action:(%s) identity(%s)' % (rtype,
                                                        action,
                                                        identity))

    def handle(self, req_msg, title, **kargs):
        # if program is shutting down, notify frontend with special reply
        # title is request type
        return handle_sync_message(False, self._handle, req_msg)

    # @graylog
    def _handle(self, req_msg):
        """ @return reply message """
        # decode to request object
        req = json_load(req_msg)

        # record receive request
        logger.info("request received [%s]" % req_msg)
        start_time = time.time()

        # discard none type request
        if req is None or not isinstance(req, dict):
            logger.error("illegal request, try it again [%s]" % req_msg)
            return return_error(req, Error(INTERNAL_ERROR,
                                           ERR_MSG_ILLEGAL_REQUEST))

        # validate request
        ret = ServiceHandler._validate(req)
        if 0 != ret:
            logger.error("validate request [%s] failed" % req_msg)
            return return_error(req, Error(INTERNAL_ERROR,
                                           ERR_MSG_VALIDATE_REQUEST_FAILED))

        # "action" is mandatory field in request.
        if "action" not in req:
            logger.error("request without action field [%s]" % req_msg)
            return return_error(req, Error(INTERNAL_ERROR,
                                           ERR_MSG_MISSING_PARAMETER,
                                           "action"))
        action = req["action"]

        # ACTION_HANDLER_MAP map the action to the corresponding handler
        if action not in self.handle_map:
            logger.error("sorry, we can't handle this request [%s]" % req_msg)
            return return_error(req, Error(INVALID_REQUEST_FORMAT,
                                           ERR_MSG_CAN_NOT_HANDLE_REQUEST))

        # handle it
        try:
            rep = self.handle_map[action](req)
        except Exception as e:
            logger.exception("handle request failed, req: {req}, reason: "
                             "{reason}".format(req=req, reason=e))
            return return_error(req, Error(INTERNAL_ERROR))
        logger.debug("handle request success, req: {req}, rep: {rep}"
                     "".format(req=req, rep=rep))

        # logging request
        end_time = time.time()
        elapsed_time = end_time - start_time
        if int(elapsed_time) >= LONG_HANDLE_TIME:
            logger.critical("handled request [%s], exec_time is [%.3f]s"
                            % (req, elapsed_time))
        else:
            logger.info("handled request [%s], exec_time is [%.3f]s"
                        % (ServiceHandler._serialize(req), elapsed_time))
        return rep
