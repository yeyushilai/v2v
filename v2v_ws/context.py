# -*- coding: utf-8 -*-

"""
Created on 2012-5-5

@author: yunify
"""

import os
from log.logger import logger
from utils.yaml_tool import yaml_load
from constants import (
    # TIMEOUT_FRONT_GATE_FAST_RATE,
    # TIMEOUT_FRONT_GATE_FAST,
    API_SECURE_PORTS,
)


class WSContext(object):
    """ thread context for ws server
    """
    def __init__(self):
        self.conf_file = None

        self.conf = None

        # memcache client
        self.mcclient = None

    def get_server_conf(self):
        if not self.conf:
            # get config
            if self.conf_file != "":
                if not os.path.isfile(self.conf_file):
                    logger.error("config file [%s] not exist" % self.conf_file)
                    return

                with open(self.conf_file, "r") as fd:
                    self.conf = yaml_load(fd).get('ws_server', None)

    def __getattr__(self, attr):
        # get conf short cut
        try:
            self.get_server_conf()
            if self.conf:
                if attr == "iaas_client_conf":
                    return self.conf['iaas_client_conf']
                if attr == "secure_ports":
                    return self.conf.get('secure_ports', API_SECURE_PORTS)
                if attr == "zone_id":
                    return self.conf.get('zone_id')
                if attr == "enable_find_fg_with_zk":
                    return self.conf.get('enable_find_fg_with_zk', False)
                if attr == "check_access_limit":
                    return self.conf.get('check_access_limit', False)
                if attr == "verify_signature_via_iam":
                    return self.conf.get('verify_signature_via_iam', True)

                # if attr == "fg_req_fast_timeout":
                #     return self.conf.get('fg_req_fast_timeout',
                #                          TIMEOUT_FRONT_GATE_FAST)
                # if attr == "fg_req_fast_timeout_rate":
                #     return self.conf.get('fg_req_fast_timeout_rate',
                #                          TIMEOUT_FRONT_GATE_FAST_RATE)
        except Exception as _:
            pass

        return None


g_ws_ctx = WSContext()


def instance():
    """ get webservice context """
    global g_ws_ctx
    return g_ws_ctx
