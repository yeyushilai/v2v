# -*- coding: utf-8 -*-

import os

from log.logger import logger
from utils.yaml_tool import yaml_load


class FGContext(object):
    """ thread context for Front Gate """

    def __init__(self):
        self.zk = None
        self.v2v_pg = None
        self.zone_pg = None
        self.iaas = None
        self.redis = None
        self.pgm = None
        self.conf_file = None
        self.conf = None

        # front gate server port
        self.server_port = 0

        # compute server port
        self.compute_server_port = 0

        # program pid
        self.pid = None

        # context related to brokers
        # lock
        self.lock = None
        # brokers
        self.brokers = None
        # allocated ports of brokers
        self.ports = None
        # interval to check the status of brokers in seconds
        self.broker_check_interval = None
        # the time out for broker to maintain an established connection
        self.broker_server_timeout = None
        # the time out for broker to wait for the first client to connect
        self.broker_client_timeout = None
        # valid broker port range
        self.broker_port_start = None
        self.broker_port_end = None

        # bot info
        self.bot_id = None

        # uuid check
        self.checker = None

        # shared multiple client
        self.mpclient = None

    def get_server_conf(self):
        if not self.conf:
            # get fg config
            if self.conf_file != "":
                if not os.path.isfile(self.conf_file):
                    logger.error("config file [%s] not exist" % self.conf_file)
                    return
                with open(self.conf_file, "r") as fd:
                    self.conf = yaml_load(fd).get('fg_server', None)

    def __getattr__(self, attr):
        # get conf short cut
        try:
            self.get_server_conf()
            if self.conf:
                if attr == "zone_id":
                    # todo: 这里可能有问题，毕竟之前是self.conf["fg_server"]取值
                    return self.conf.get('zone_id', None)

        except Exception as _:
            pass
        return None


g_fg_ctx = FGContext()


def instance():
    # type: () -> object
    """ get front gate context """
    global g_fg_ctx
    return g_fg_ctx
