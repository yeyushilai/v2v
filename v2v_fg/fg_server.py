#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import signal
import sys
import time
import threading
import traceback

from log.logger_name import set_logger_name
set_logger_name("v2v_fg_server")
from server.locator import set_global_locator
from log.logger import logger

from comm.base_server import BaseServer
from comm.base_client import BaseClient
from comm.pull_server import PullServer
from comm.multipeer_client import MultiPeerClient
from server.shutdown.helper import on_gracefully_shutdown
from pull_handler import PullServiceHandler
from service_handler import ServiceHandler
from optparse import OptionParser
from db.pg_model import PGModel
from db.constants import (
    DB_ZONE,
    DB_V2V,
    KEYSPACE_USERDATA_ATTACHMENT,
    KEYSPACE_JOB_LOG
)
from mc.mc_model import MCModel
from zk.dlocator import DLocator
from zk.dqueue import DQueue
from utils.pitrix_folder import PitrixFolder
from utils.net import get_hostname
from utils.global_conf import (
    get_pg,
    get_redis,
    get_ca,
    get_zk,
    connect_zk,
    get_mc,
    get_server_conf
)
from utils.constants import WEB_SERVICE_HAPROXY_PORT as IAAS_WS_HAPROXY_PORT
from utils.constants import FRONT_GATE_PROXY_PORT as IAAS_FG_HAPROXY_PORT
from utils.constants import SERVER_TYPE_V2V_FRONT_GATE
from utils.constants import V2V_FRONT_GATE_PORT
from utils.net import get_listening_url
# from utils.id_tool import UUIDPGChecker
from utils.yaml_tool import yaml_load
from utils.misc import (
    exit_program,
    dump_program_stacks,
    dump_program_objects,
    initialize_program
)

from fg import context
from fg.constants import (
    V2V_JOB_QUEUE_PATH,
    REDIS_CONFIG_NAME_V2V
)
from fg.resource_control.iaas import interface
from fg.uutils.utils_push import (
    push_event_insert_trigger,
    push_event_update_trigger
)

ctx = context.instance()


class FrontGate(object):
    """ front gate, sits between the web service and the backend system"""

    def __init__(self, conf, pattern=None):
        """ constructor """

        # initialization calls
        initialize_program()

        self.conf = conf

        # threads handlers
        self.thrs = []

        # create working folders if not present
        PitrixFolder.build()
        if pattern and pattern == "local":
            PitrixFolder.CONF_HOME = "/pitrix/new_testing_conf"
        # initialize context
        ctx.pull_url = "inproc://pullserver_%d" % id(self)
        # todo: delete this? ctx.compute_server_port = COMPUTE_SERVER_PORT

        # bot info
        ctx.bot_id = "%s" % (get_hostname())

        # shared multiple client
        ctx.mpclient = MultiPeerClient()
        ctx.mpclient.init()

        # shared base client
        ctx.client = BaseClient(use_sock_pool=True)

    def _get_live_thr_cnt(self):
        """ return the sum of threads that lives """

        live_cnt = 0
        for thr in self.thrs:
            if thr.is_alive():
                live_cnt += 1

        return live_cnt

    @staticmethod
    def _zk_disconnect_cb():
        """ callback when zookeeper is disconnected """
        # stop locator service
        ctx.locator.stop()

    @staticmethod
    def _zk_connect_cb():
        """ callback when zookeeper is connected """
        # start locator service
        ctx.locator.start(ctx.zk)

        # register self as server
        ctx.locator.register(SERVER_TYPE_V2V_FRONT_GATE, get_hostname(),
                             V2V_FRONT_GATE_PORT)

        # initiation of distributed queue, for v2v service job
        ctx.dq_v2v = DQueue(ctx.zk, V2V_JOB_QUEUE_PATH)
        logger.info("DQueue initialized")

    def _get_qing_cloud(self):
        if self.conf.get("fg_server") and self.conf.get("fg_server").get("iaas_client_conf"):
            iaas_client_conf = self.conf.get("fg_server").get("iaas_client_conf")
            return interface.QingCloud(iaas_client_conf)
        return None

    def start(self):
        # connect to postgresql db v2v
        ctx.v2v_pg = get_pg(DB_V2V, maxconn=50)
        if not ctx.v2v_pg:
            logger.error("connect to PostgreSQL failed: can't connect "
                         "database %s" % DB_V2V)
            exit_program(-1)
        ctx.pgm = PGModel(ctx.v2v_pg)
        ctx.v2v_pg.add_insert_trigger(push_event_insert_trigger)
        ctx.v2v_pg.add_update_trigger(push_event_update_trigger)

        # connect to postgresql db zone
        ctx.zone_pg = get_pg(DB_ZONE, maxconn=50)
        if not ctx.zone_pg:
            logger.error("connect to PostgreSQL failed, can't connect "
                         "database %s" % DB_ZONE)

        # connect to cassandra job logs
        ctx.ca_job_log = get_ca(KEYSPACE_JOB_LOG)
        if ctx.ca_job_log is None:
            logger.error("connect to cassandra [%s] failed: can't connect",
                         KEYSPACE_JOB_LOG)
            exit_program(-1)

        # connect to cassandra user data attachment
        ctx.ca_uda = get_ca(KEYSPACE_USERDATA_ATTACHMENT)
        if ctx.ca_uda is None:
            logger.error("connect to cassandra [%s] failed: can't connect",
                         KEYSPACE_USERDATA_ATTACHMENT)
            exit_program(-1)

        # get zone id
        ctx.server_conf = get_server_conf()
        ctx.iaas_ws_proxy_port = IAAS_WS_HAPROXY_PORT
        ctx.iaas_fg_proxy_port = IAAS_FG_HAPROXY_PORT

        # uuid checker
        # ctx.checker = UUIDPGChecker(ctx.pg)
        # ctx.cw_checker = UUIDPGChecker(ctx.pg_cw)

        # redis
        ctx.redis = get_redis(REDIS_CONFIG_NAME_V2V)

        # iaas
        ctx.iaas = self._get_qing_cloud()

        # zk
        ctx.locator = DLocator()
        ctx.zk = get_zk(self._zk_connect_cb, self._zk_disconnect_cb)
        if 0 != connect_zk(ctx.zk):
            logger.error("connect to zookeeper failed: can't connect")
            exit_program(-1)
        set_global_locator(ctx.locator)

        # connect to memcached
        ctx.mcclient = get_mc()
        if not ctx.mcclient:
            logger.error("connect to memcached failed: can't connect")
            exit_program(-1)
        ctx.mcm = MCModel(ctx.mcclient)

        # start peer task to handle requests from other bots
        logger.info("starting service handler ...")
        handler = ServiceHandler()
        peer_server = BaseServer(get_listening_url(SERVER_TYPE_V2V_FRONT_GATE), 1,
                                 handler)
        peer_thr = threading.Thread(target=peer_server.start, args=())
        peer_thr.setDaemon(True)
        peer_thr.start()
        self.thrs.append(peer_thr)

        # start pull server to handle internal sink requests
        logger.info("starting pull service handler ...")
        handler = PullServiceHandler()
        pull_server = PullServer(ctx.pull_url, 1, handler)
        pull_thr = threading.Thread(target=pull_server.start, args=())
        pull_thr.setDaemon(True)
        pull_thr.start()
        self.thrs.append(pull_thr)

        # wait while servers are actually started
        time.sleep(1)
        logger.info("front gate is running now.")

        # 1) if KeyboardInterrupt, quit
        # 2) if one of the threads dead, quit
        try:
            while self._get_live_thr_cnt() == len(self.thrs):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("interrupted, quit now")
            exit_program(-1)


def _get_opt_parser():
    """ get option parser """

    MSG_USAGE = "front_gate [-c <conf_file>]"
    opt_parser = OptionParser(MSG_USAGE)

    opt_parser.add_option("-c", "--config", action="store", type="string",
                          dest="conf_file", help='config file', default="")

    opt_parser.add_option("-p", "--pattern", action="store", type="string",
                          dest="pattern", help='pattern', default="")

    return opt_parser


def main():
    """ start up a server and wait for request """

    # parser options
    parser = _get_opt_parser()
    (options, _) = parser.parse_args(sys.argv)

    # get config
    conf = {}
    if options.conf_file != "":
        if not os.path.isfile(options.conf_file):
            logger.error("config file [%s] not exists" % options.conf_file)
            sys.exit(-1)

        with open(options.conf_file, "r") as fd:
            conf = yaml_load(fd)

    # receive signal and handler it properly
    signal.signal(signal.SIGTERM, on_gracefully_shutdown)
    signal.signal(signal.SIGINT, on_gracefully_shutdown)
    signal.signal(signal.SIGUSR1, dump_program_stacks)
    signal.signal(signal.SIGUSR2, dump_program_objects)

    fg_ser = FrontGate(conf, options.pattern)
    # noinspection PyBroadException
    try:
        fg_ser.start()
    except Exception as e:
        print e
        logger.error("Exit with exception: %s" % traceback.format_exc())
        exit_program(-1)


if __name__ == '__main__':
    main()
