# -*- coding: utf-8 -*-

import six

from log.logger import logger
import connexion as connexion
from api.error import Error
from api.return_tools import return_error
from constants import (
    ACTION_V2V_SRC_PLATFORM_CHECK_SRC_PLATFORM_CONNECTIVITY,
    ACTION_V2V_SRC_PLATFORM_ADD_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_UPDATE_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_DELETE_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM,
    ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM
)
from handlers.controllers.common import (
    process_query_list_param,
    validate_user_request,
    handle_send_fg_request,
)
from handlers.impl.src_platform_impl import (
    handle_check_src_platform_connectivity_local,
    handle_add_src_platform_local,
    handle_delete_src_platform_local,
    handle_describe_src_platform_vm_local,
    handle_describe_src_platform_local,
    handle_update_src_platform_local,
)

from utils.misc import format_params


def check_src_platform_connectivity(**kwargs):
    """check_src_platform_connectivity"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("check_src_platform_connectivity with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_SRC_PLATFORM_CHECK_SRC_PLATFORM_CONNECTIVITY
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_check_src_platform_connectivity_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("check_src_platform_connectivity send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("check_src_platform_connectivity get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "check_src_platform_connectivity get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def add_src_platform(**kwargs):
    """add_src_platform"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("add_src_platform with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_SRC_PLATFORM_ADD_SRC_PLATFORM
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_add_src_platform_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("add_src_platform send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("add_src_platform get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "add_src_platform get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def update_src_platform(**kwargs):
    """update_src_platform"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("update_src_platform with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_SRC_PLATFORM_UPDATE_SRC_PLATFORM
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_update_src_platform_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("update_src_platform send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("update_src_platform get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "update_src_platform get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def delete_src_platform(**kwargs):
    """delete_src_platform"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("delete_src_platform with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_SRC_PLATFORM_DELETE_SRC_PLATFORM
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_delete_src_platform_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("delete_src_platform send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("delete_src_platform get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "delete_src_platform get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def describe_src_platform(**kwargs):
    """Get src_platformGet src_platform"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("describe_src_platform with req params: [%s]"
                 % format_params(kwargs))

    action = ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_describe_src_platform_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("describe_src_platform send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("describe_src_platform get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug("describe_src_platform get local handle rsp: msg=[%s] code=[%s]"
                     % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def describe_src_platform_vm(**kwargs):
    """Get src_platformlist vm in cluster of src_platform"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("describe_src_platform_vm with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_describe_src_platform_vm_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("describe_src_platform_vm send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("describe_src_platform_vm get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "describe_src_platform_vm get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code
