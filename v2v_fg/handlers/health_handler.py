# -*- coding: utf-8 -*-

from log.logger import logger

from fg import context
from fg.return_tools import return_success
from fg.constants import ACTION_V2V_HEALTH_HEALTH_CHECK


CTX = context.instance()


def handle_health_check(req):
    """健康检查"""
    logger.debug('handle health check start, {}'.format(req))
    rsp = {"data": "health check pass"}
    return return_success(req, rsp)


HANDLER_MAP = {
    ACTION_V2V_HEALTH_HEALTH_CHECK: handle_health_check
}
