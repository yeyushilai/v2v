# -*- coding: utf-8 -*-

import random
from utils.misc import (
    explode_array,
)
from utils.time_stamp import (
    get_expired_ts,
    get_ts,
)
from api.constants import (
ACTION_REDIRECT_TO_SERVICE_FRONTGATE,
CLOUD_SVC_TYPE_V2V
)

from comm.base_client import ReqLetter
from utils.json import json_dump, json_load
from utils.constants import (
    V2V_FRONT_GATE_PORT,
    FRONT_GATE_HAPROXY_PORT
)
from log.logger import logger
from random import choice

import context
from common.misc import get_fg_servers, generate_id
from resource_control.iaas.zone import (
    dispatch_region_request,
)
from resource_control.iaas.interface import (
    get_all_zones,
)
from constants import (
    REQ_EXPIRED_INTERVAL,
    ZONE_STATUS_FAULTY,
    TIMEOUT_FRONT_GATE,
)


def get_fg_timeout():
    # """
    #     if network congestion happened between ws and one of the fg_servers,
    #     the ws_server workers will be full due to request timeout.
    #     We will monitor request timeout from current active workers and adjust
    #      request timeout dynamically to avoid request congestion.
    #     Shorten request timeout can speed up request consumption.
    # """
    # ctx = context.instance()
    # peer_server = ctx.peer_server
    # active_worker = len(peer_server.worker_threads) - \
    #                 len(peer_server.available_workers)
    # active_rate = int(float(active_worker) / peer_server.max_worker_num * 100)
    #
    # # if active rate large than 80%, we consider ws_server is busy
    # logger.debug("fg timeout [avail:%s|active:%s|rate:%s|Total:%s]"
    #              % (len(peer_server.available_workers), active_worker,
    #                 active_rate, peer_server.max_worker_num))
    # if active_rate > ctx.fg_req_fast_timeout_rate:
    #     logger.info("fg timeout [%s|%s|%s]" % (active_worker, active_rate,
    #                                            peer_server.max_worker_num))
    #     return ctx.fg_req_fast_timeout
    return TIMEOUT_FRONT_GATE


def get_zone(zone_id):
    all_zones = get_all_zones()
    if not all_zones:
        logger.error("get zones failed")
        return None
    return all_zones.get(zone_id)


def get_random_fg(zone_id):
    """ fetch a random front gate """
    # get the front gate to specified zone
    zone = get_zone(zone_id)
    if zone is None:
        logger.error("get zone for [%s] failed" % zone_id)
        return None
    if zone["status"] == ZONE_STATUS_FAULTY:
        logger.error("zone [%s] is faulty", zone_id)
        return None
    return random.choice(explode_array(zone['front_gates']))


g_fg_server = {}


def send_fg_request(zone_id, req, need_reply=True, suppress_critical=False):
    """ send request to zone
        @param zone_id : the ID of zone you want to send request to.
        @param req : request to send.
        @param need_reply : if the reply of the request if needed, set to True;
                            otherwise, set it to False.
        @param suppress_critical : whether suppress critical or not.
    """
    ctx = context.instance()

    if 'zone' not in req:
        req['zone'] = zone_id

    if 'sender' in req:
        dispatch_region_request(req, req['sender'])
        zone_id = req['zone']

    logger.info(ctx.conf)
    logger.info(ctx.zone_id)

    if ctx.zone_id and ctx.enable_find_fg_with_zk:
        # get fg server from zk only when no region case
        if zone_id in g_fg_server:
            zone_fg_servers = g_fg_server.get(zone_id)
        else:
            zone_fg_servers = get_fg_servers(zone_id)
            if not zone_fg_servers:
                logger.critical("get zone [%s] fg server failed", zone_id)
                return None
            g_fg_server.update({zone_id: zone_fg_servers})
        host = choice(zone_fg_servers)
        port = V2V_FRONT_GATE_PORT
    else:
        # get the front gate to specified zone from iaas api, which will
        #  send req to global iaas ws to get zone iaas-fg.
        front_gate = get_random_fg(zone_id)
        if front_gate is None:
            if suppress_critical:
                logger.error("get front_gate for [%s] failed" % zone_id)
            else:
                logger.critical("get front_gate for [%s] failed" % zone_id)
            return None

        # get front gate proxy host and port
        items = front_gate.split(":")
        if len(items) == 2:
            host = items[0]
            port = items[1]
        elif len(items) == 1:
            host = front_gate
            port = FRONT_GATE_HAPROXY_PORT
        else:
            logger.critical("illegal front gate [%s] failed" % front_gate)
            return None

    # add expires
    if "expires" not in req:
        req["expires"] = get_expired_ts(get_ts(), REQ_EXPIRED_INTERVAL)

    # send request
    if ctx.pattern == "local":
        host = "127.0.0.1"

    req["req_id"] = generate_id()
    if not ctx.enable_find_fg_with_zk:
        req = {
            'action': ACTION_REDIRECT_TO_SERVICE_FRONTGATE,
            'svc_type': CLOUD_SVC_TYPE_V2V,
            'svc_fg_req': req,
            'sender': req['sender'],
            'expires': req["expires"],
            'need_reply': need_reply,
        }
    logger.info("sending request [%s] to front gate [%s:%s]" % (req, host, port))
    letter = ReqLetter("tcp://%s:%s" % (host, port), json_dump(req))

    if not need_reply:
        return ctx.client.send(letter, 0, get_fg_timeout())
    rep = json_load(ctx.client.send(letter, 0, get_fg_timeout()))
    if rep is None:
        logger.error("receive reply failed on [%s:%s]" % (host, port))
        return None
    return rep
