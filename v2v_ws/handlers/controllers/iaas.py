# -*- coding: utf-8 -*-

import six

from utils.misc import format_params
from api.return_tools import return_error
from log.logger import logger
from api.error import Error
import connexion as connexion
from constants import (
    ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES,
    ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES_PG_RULE
)
from handlers.controllers.common import (
    process_query_list_param,
    validate_user_request,
    handle_send_fg_request,
)
from handlers.impl.iaas_impl import (
    handle_describe_iaas_hyper_nodes_local,
    handle_describe_iaas_hyper_nodes_pg_rule_local
)


def describe_iaas_hyper_nodes(**kwargs):
    """Get src_platform_clusterGet src_platform_cluster"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("describe_iaas_hyper_nodes with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_describe_iaas_hyper_nodes_local(kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("describe_iaas_hyper_nodes send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("describe_iaas_hyper_nodes get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "describe_iaas_hyper_nodes get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


def describe_iaas_hyper_nodes_pg_rule(**kwargs):
    """
        describe_iaas_hyper_nodes_pg_rule"""
    if "Channel" in connexion.request.headers:
        kwargs["channel"] = connexion.request.headers["Channel"]
    process_query_list_param(kwargs, connexion.request.args)
    logger.debug("describe_iaas_hyper_nodes_pg_rule with req params: [%s]"
                 % format_params(kwargs))

    if 'body' in kwargs:
        del kwargs['body']
        body = connexion.request.get_json()
        if body:
            for k, v in six.iteritems(body):
                kwargs[k] = v

    action = ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES_PG_RULE
    kwargs.update({'action': action})
    valid_user, error = validate_user_request(kwargs,
                                              connexion.request)
    if not valid_user:
        return return_error(kwargs, error, dump=False)

    need_send_fg, ret_msg, ret_code = handle_describe_iaas_hyper_nodes_pg_rule_local(
        kwargs)
    if isinstance(ret_msg, Error):
        return return_error(kwargs, ret_msg, dump=False)

    if need_send_fg:
        logger.debug("describe_iaas_hyper_nodes_pg_rule send req to fg with "
                     "user:[%s] params:[%s] req:[%s]"
                     % (valid_user, format_params(kwargs),
                        format_params(connexion.request)))
        rsp = handle_send_fg_request(valid_user, kwargs, connexion.request)
        logger.debug("describe_iaas_hyper_nodes_pg_rule get fg rsp: rsp=[%s]"
                     % (format_params(rsp)))
        return rsp
    else:
        logger.debug(
            "describe_iaas_hyper_nodes_pg_rule get local handle rsp: msg=[%s] code=[%s]"
            % (format_params(ret_msg), ret_code))
        return ret_msg, ret_code


