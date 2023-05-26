# -*- coding: utf-8 -*-

import time

from qingcloud.iaas.connection import APIConnection

from fg.constants import (
    DESC_USERS,
    DESC_INSTANCES,
    DESC_CLUSTER_USERS,
    DESC_BOTS,
    DESC_QUOTAS,
    DESC_VXNETS,
    GET_QUOTA_LEFT,
    DESC_PLG_RULE,
    DESC_PLG
)
from log.logger import logger

SORT_KEY = {
    DESC_INSTANCES: "instance_id",
    DESC_CLUSTER_USERS: "user_id",
}


class QingCloud(object):
    """ qingcloud sdk 实现类 """

    def __init__(self, client_conf, verb="GET"):
        self.qy_access_key = client_conf['qy_access_key_id']
        self.qy_secret_access_key = client_conf['qy_secret_access_key']
        self.host = client_conf['host']
        self.port = client_conf['port']
        self.protocol = client_conf['protocol']
        self.zone = client_conf["zone"]
        self.apiConn = None
        self.create_conn()
        self.verb = verb

    def create_conn(self):
        """ 创建qingcloud连接 """
        self.apiConn = APIConnection(qy_access_key_id=self.qy_access_key,
                                     qy_secret_access_key=self.qy_secret_access_key,
                                     zone=self.zone,
                                     host=self.host,
                                     port=self.port,
                                     protocol=self.protocol,
                                     debug=True)

    def send_request(self, action, body, api_type="other", api_connector=None):
        """发送请求"""
        if action in SORT_KEY.keys():
            body["sort_key"] = SORT_KEY[action]
        start_time = time.time()
        if api_type == "sdk":
            if api_connector is None:
                ret = getattr(self.apiConn, action)(**body)
            else:
                ret = getattr(api_connector, action)(**body)
        else:
            if api_connector is None:
                ret = self.apiConn.send_request(
                    action=action, body=body, verb=self.verb)
            else:
                ret = api_connector.send_request(action=action, body=body)
        end_time = time.time()

        gelf_props = {
            "action": action,
            "rep": ret,
            "req": body,
            "cost": end_time - start_time
        }
        if ret and ret["ret_code"] != 0:
            logger.error("call iass action {action} fail, ret code: {ret_code}"
                         "".format(action=action, ret_code=ret["ret_code"]),
                         extra={"gelf_props": gelf_props})
            return None
        logger.info("call iass action %s success" % action,
                    extra={"gelf_props": gelf_props})
        return ret

    def desc_users(self, users=None, offset=0, limit=100, verbose=0,
                   qc_api_connector=None):
        """
        desc_users
        """
        req = {
            "offset": offset,
            "limit": limit,
            "verbose": verbose,
            "zone": self.apiConn.zone
        }
        if users:
            req["users"] = users
        if qc_api_connector is None:
            return self.send_request(DESC_USERS, req)
        else:
            return qc_api_connector.sendRequest(DESC_USERS, req)

    def describe_bots(self, offset=0, limit=100, verbose=0,
                      qc_api_connector=None, status=None,
                      search_word=None, bots=None, zone=None):
        """
        desc_bots
        """
        req = {
            "offset": offset,
            "limit": limit,
            "verbose": verbose,
            "zone": self.apiConn.zone,
            "sort_key": "create_time",
            "reverse": 1
        }
        if bots:
            req["bots"] = bots
        if status:
            req["status"] = status
        if search_word:
            req["search_word"] = search_word
        if zone:
            req["zone"] = zone
        if qc_api_connector is None:
            return self.send_request(DESC_BOTS, req)
        else:
            return qc_api_connector.send_request(DESC_BOTS, req)

    def describe_quotas(self, user_id=None, offset=0, limit=100,
                        qc_api_connector=None):
        req = {
            "offset": offset,
            "limit": limit,
        }
        if user_id:
            req["users"] = user_id
        if qc_api_connector is None:
            return self.send_request(DESC_QUOTAS, req)
        else:
            return qc_api_connector.send_request(DESC_QUOTAS, req)

    def describe_vxnets(self, vxnets=None, verbose=1, limit=20, offset=0):
        req = {
            "vxnets": vxnets,
            "verbose": verbose,
            "tags": [],
            "sort_key": "",
            "control_plane": None,
            "visibility": None,
            "limit": limit,
            "offset": offset,
            "owner": [],
            "reverse": 1
        }
        return self.send_request(DESC_VXNETS, req)

    def get_quota_left(self, resource_type=None, user_id=None):
        req = {
            "resource_types": resource_type,
            "user": user_id
        }

        return self.send_request(GET_QUOTA_LEFT, req)

    def desc_place_group_rules(self, place_groups=None):
        req = {
            "place_group": place_groups
        }

        return self.send_request(DESC_PLG_RULE, req)

    def desc_place_groups(self, place_groups=None):
        req = {
            "place_groups": place_groups,
            "verbose": 1,
        }
        return self.send_request(DESC_PLG, req)
