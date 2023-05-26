# -*- coding: utf-8 -*-

import six

import connexion as connexion
from api.error import Error
from api.return_tools import return_error
from constants import (
    ACTION_V2V_MIGRATION_TASK_CREATE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_UPDATE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DELETE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DETAIL_MIGRATION_TASK,
    ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_VM
)
from handlers.controllers.common import (
    process_query_list_param,
    validate_user_request,
    handle_send_fg_request,
)
from handlers.impl.migration_task_impl import (
    handle_create_migration_task_local,
    handle_update_migration_task_local,
    handle_delete_migration_task_local,
    handle_describe_migration_task_local,
    handle_detail_migration_task_local,
    handle_describe_migration_vm_local

)
from log.logger import logger
from utils.misc import format_params


def create_migration_task(**kwargs):
    """create_migration_task"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("create_migration_task with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_MIGRATION_TASK_CREATE_MIGRATION_TASK
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_create_migration_task_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("create_migration_task send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("create_migration_task get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "create_migration_task get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def update_migration_task(**kwargs):
    """update_migration_task"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("update_migration_task with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_MIGRATION_TASK_UPDATE_MIGRATION_TASK
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_update_migration_task_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("update_migration_task send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("update_migration_task get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "update_migration_task get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def delete_migration_task(**kwargs):
    """delete_migration_task"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("delete_migration_task with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_MIGRATION_TASK_DELETE_MIGRATION_TASK
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_delete_migration_task_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("delete_migration_task send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("delete_migration_task get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "delete_migration_task get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def describe_migration_task(**kwargs):
    """Get Migrate Task List"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("describe_migration_task with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_TASK
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_describe_migration_task_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("describe_migration_task send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("describe_migration_task get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "describe_migration_task get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def detail_migration_task(**kwargs):
    """detail_migration_task"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("detail_migration_task with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_MIGRATION_TASK_DETAIL_MIGRATION_TASK
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_detail_migration_task_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("detail_migration_task send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("detail_migration_task get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "detail_migration_task get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def describe_migration_vm(**kwargs):
    """describe_migration_vm"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("describe_migration_vm with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_VM
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_describe_migration_vm_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("describe_migration_vm send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("describe_migration_vm get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "describe_migration_vm get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code
