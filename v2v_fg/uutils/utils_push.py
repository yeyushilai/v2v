# -*- coding: utf-8 -*-

from log.logger import logger
from utils.constants import SERVER_TYPE_WEBSOCKET_PUSH
from utils.json import json_dump
from utils.net import get_mgmt_net_ip
from utils.time_stamp import format_utctime
from api.common import get_event_type
from api.constants import CONTROLLER_SELF
from api.constants import (
    REQ_PUSH_EVENT,
    TYPE_RESOURCE_CREATION,
    MGMT_USER_ID,
    TYPE_RESOURCE_UPDATE,
)
from comm.base_client import ReqLetter
from db.constants import (
    CREATE_EVENT_TABLES,
    PUBLIC_COLUMNS,
    INDEXED_COLUMNS,
    UPDATE_EVENT_COLUMNS,
    TB_ROUTER
)

from fg import context
from fg.job import decorate_job
from fg.constants import (
    TB_JOB,
    TIMEOUT_PUSH_EVENT
)


def send_push_request(req, timeout=TIMEOUT_PUSH_EVENT):
    """
    send request to push server
    :param req:
    :param timeout:
    :return:
    """
    ctx = context.instance()
    server = ctx.locator.get_random_server(SERVER_TYPE_WEBSOCKET_PUSH)
    if server is None:
        logger.error("get server [%s] failed" % SERVER_TYPE_WEBSOCKET_PUSH)
        return

    # send request to push server
    (host, port) = server
    logger.debug("sending request [%s] to push server [%s]" % (req, host))
    letter = ReqLetter("tcp://%s:%s" % (get_mgmt_net_ip(host), port),
                       json_dump(req))
    return ctx.client.send(letter, timeout=timeout)


def push_event(user_id, event, resource_id=None):
    """
     push events to push server
    :param user_id:
    :param event:
    :param resource_id:
    :return:
    """
    ctx = context.instance()

    user_ids = set()
    user_ids.add(user_id)

    # push events to push server
    topic = ["user", "event", ctx.zone_id, user_id]
    req = {
        'req_type': REQ_PUSH_EVENT,
        'topic': topic,
        'data': event,
        'resource_id': resource_id,
    }
    send_push_request(req)
    return


def push_event_insert_trigger(table, columns):
    ctx = context.instance()
    # push event when needed
    if table not in CREATE_EVENT_TABLES:
        return

    # get owner
    primary_key = INDEXED_COLUMNS[table][0]
    key = columns[primary_key] if primary_key in columns else None
    row = ctx.zone_pg.get(table, key, ['owner', 'controller'])
    if row is None or row['controller'] != CONTROLLER_SELF:
        return
    user_id = row['owner']

    # get push columns
    public_cols = columns.keys() if user_id == MGMT_USER_ID \
        else PUBLIC_COLUMNS[table]
    push_cols = {}

    # decorate job specially
    if table == TB_JOB:
        if "directive" in columns and "directive" not in public_cols:
            public_cols.append("directive")

    for col in public_cols:
        if col in columns:
            push_cols[col] = format_utctime(columns[col])
    if len(push_cols) == 0:
        return

    # normal user not allowed to obtain job "directive"
    if table == TB_JOB:
        push_cols = decorate_job(push_cols)
        if user_id != MGMT_USER_ID:
            if "directive" in push_cols:
                del push_cols["directive"]

    # push event
    event = {
        'type': TYPE_RESOURCE_CREATION,
        'rtype': get_event_type(table),
        'resource_set': [push_cols],
    }
    push_event(user_id, event, resource_id=key)

    return


def push_event_update_trigger(table, key, columns):
    ctx = context.instance()
    # push event when needed
    if table not in UPDATE_EVENT_COLUMNS:
        return
    push_cols = {}
    for col in columns.keys():
        if col in UPDATE_EVENT_COLUMNS[table] or 'name' in col \
                or col == 'description':
            push_cols[col] = format_utctime(columns[col])
    if len(push_cols) == 0:
        return

    # get owner
    row = ctx.zone_pg.get(table, key, ['owner', 'controller'])
    if row is None or row['controller'] != CONTROLLER_SELF:
        return
    user_id = row['owner']

    # push event
    push_cols.update({INDEXED_COLUMNS[table][0]: key})
    if table == TB_ROUTER:
        if "group_id" in push_cols:
            push_cols["security_group_id"] = push_cols["group_id"]
            del push_cols["group_id"]
    event = {
        'type': TYPE_RESOURCE_UPDATE,
        'rtype': get_event_type(table),
        'resource_set': [push_cols],
    }
    push_event(user_id, event, resource_id=key)
    return
