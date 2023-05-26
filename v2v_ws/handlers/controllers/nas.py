# -*- coding: utf-8 -*-

import six
from utils.misc import (
    format_params,
)
from api.return_tools import return_error
from log.logger import logger
from api.error import Error

import connexion as connexion
from constants import (
    ACTION_V2V_NAS_CHECK_NAS_CONNECTIVITY,
    ACTION_V2V_NAS_PARSE_VMS_FROM_NAS
)
from handlers.controllers.common import (
    process_query_list_param,
    validate_user_request,
    handle_send_fg_request,
)
from handlers.impl.nas_impl import (
    handle_check_nas_connectivity_local,
    handle_parse_vms_from_nas_local,
)


def check_nas_connectivity(**kwargs):
    """check_nas_connectivity"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("check_nas_connectivity with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_NAS_CHECK_NAS_CONNECTIVITY
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_check_nas_connectivity_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("check_nas_connectivity send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("check_nas_connectivity get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "check_nas_connectivity get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def parse_vms_from_nas(**kwargs):
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("parse_vms_from_nas with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_NAS_PARSE_VMS_FROM_NAS
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_parse_vms_from_nas_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("parse_vms_from_nas send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("parse_vms_from_nas get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "parse_vms_from_nas get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


