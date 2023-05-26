# -*- coding: utf-8 -*-

import hashlib
import random
import time

import context
from constants import (
    SERVER_TYPE_IAM_SIGNATURE,
    IAM_SIGNATURE_SERVER_PROXY_PORT,
    ZONE_SERVER_CACHE_TIME,
    MC_DEFAULT_CACHE_TIME,
)
from utils.constants import (
    SERVER_TYPE_V2V_FRONT_GATE,
    V2V_FRONT_GATE_PORT
)
from utils.lru_cache import LRUCache
from utils.net import is_port_open

g_server_cache = LRUCache(16)


def _get_servers(server_type, port, zone_id=None):
    """
    get servers from a zone
    """

    key = "%s_s_%s" % (server_type, zone_id)

    servers = g_server_cache.get(key)
    if servers:
        servers_ok = True
        for server in servers:
            if server and not is_port_open(server, port):
                servers_ok = False
                break
        if servers_ok:
            return servers

    ctx = context.instance()
    server_ports = None
    # if zone_id and zone_id == ctx.zone_id:
    if ctx.locator:
        # shortcut for local zone
        server_ports = ctx.locator.get_servers(server_type)

    if server_ports:
        servers = [server for server, _ in server_ports]
        g_server_cache.set(key,
                           servers,
                           ZONE_SERVER_CACHE_TIME)
    return servers


def get_fg_servers(zone_id):
    """
    get fg servers from a zone
    """
    return _get_servers(SERVER_TYPE_V2V_FRONT_GATE,
                        V2V_FRONT_GATE_PORT, zone_id)


def get_iam_signature_servers():
    """
    get fg servers from a zone
    """
    ctx = context.instance()
    return _get_servers(SERVER_TYPE_IAM_SIGNATURE,
                        IAM_SIGNATURE_SERVER_PROXY_PORT,
                        ctx.zone_id)


def get_cache(prefix, key):
    ctx = context.instance()

    return ctx.mcm.get(prefix, key)


def set_cache(prefix, key, val, cache_time=MC_DEFAULT_CACHE_TIME):
    ctx = context.instance()
    return ctx.mcm.set(prefix, key, val, time=cache_time)


def unset_cache(prefix, key):
    ctx = context.instance()

    return ctx.mcm.delete(prefix, key)


PARAMS_TO_FORMAT = ["passwd", "newpasswd", "oldpasswd", "new_passwd",
                    "old_passwd", "attachment_content", "private_key",
                    "certificate_content",
                    "icp_password", "data", "substances", "register_info",
                    "error_msg", "transition_substance", "user_config",
                    "package_content", "login_passwd"]


def is_str(value):
    """ check if value is a string """
    if (not isinstance(value, str)) and (not isinstance(value, unicode)):
        return False
    return True


def format_params(req):
    """ format request output"""
    # if not isinstance(req, dict):
    #     return None
    #
    # new_req = copy.deepcopy(req)
    # for k, v in new_req.items():
    #     if isinstance(v, dict):
    #         for key in v:
    #             if key in PARAMS_TO_FORMAT:
    #                 v[key] = "*"
    #     elif is_str(v):
    #         if k in PARAMS_TO_FORMAT:
    #             new_req[k] = "*"
    return req


def rand_str(num=10):
    return "".join(
        random.sample(
            "ABCDEFGHJKLMNPQRSTUVWXY23456789ABCDEFGHJKLMNPQRSTUVWXY23456789abcdefghjkmnpqrstuvwxy23456789abcdefghjkmnpqrstuvwxy23456789",
            num))  # noqa


def md5(s):
    if type(s) == str:
        s = s.encode("utf-8")
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def generate_id():
    s = "%s%s" % (int(time.time() * 10000), rand_str())
    return md5(s.encode('utf-8'))[8:24]
