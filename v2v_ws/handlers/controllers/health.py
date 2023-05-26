# -*- coding: utf-8 -*-

from utils.misc import format_params
from api.return_tools import return_error
from log.logger import logger
from api.error import Error

import connexion as connexion
from constants import ACTION_V2V_HEALTH_HEALTH_CHECK
from handlers.controllers.common import (
    process_query_list_param,
    validate_user_request,
    handle_send_fg_request,
)
from handlers.impl.health_impl import (
    handle_health_check_local
)


def health_check(**kwargs):
    """Health Check健康检查"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("health_check with req params: [%s]"
                 % format_params(kwargs))

    action = ACTION_V2V_HEALTH_HEALTH_CHECK
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_health_check_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("health_check send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("health_check get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug("health_check get local handle rsp: msg=[%s] code=[%s]"
                     % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code
