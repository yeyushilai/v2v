# -*- coding: utf-8 -*-

from uutils.zk.interface import ZKInterface
from uutils.pg.interface import V2VPGInterface, ZonePGInterface
from uutils.redis.interface import V2VRedisInterface
from resource_control.iaas.interface import IAASInterface
from uutils.common import singleton
from constants.common import (
    # 当前节点信息
    LOCAL_NODE_ID,

    # 配置信息
    V2V_WORKER_YAML_CONFIG
)
from constants.iaas import SERVER_CONF


@singleton
class WorkerContext(object):
    """ Worker Context类"""

    def __init__(self):
        self._v2v_conf = None
        self._server_conf = None
        self._zookeeper_conf = None
        self._redis = None
        self._zk = None
        self._v2v_pg = None
        self._zone_pg = None
        self._iaas = None
        self._node = None

    @property
    def v2v_conf(self):
        if self._v2v_conf is None:
            self._v2v_conf = V2V_WORKER_YAML_CONFIG
        return self._v2v_conf

    @property
    def server_conf(self):
        if self._server_conf is None:
            self._server_conf = SERVER_CONF
        return self._server_conf

    @property
    def zk(self):
        if self._zk is None:
            self._zk = ZKInterface()
        return self._zk

    @property
    def v2v_pg(self):
        if self._v2v_pg is None:
            self._v2v_pg = V2VPGInterface()
        return self._v2v_pg

    @property
    def zone_pg(self):
        if self._zone_pg is None:
            self._zone_pg = ZonePGInterface()
        return self._zone_pg

    @property
    def redis(self):
        if self._redis is None:
            self._redis = V2VRedisInterface()
        return self._redis

    @property
    def iaas(self):
        if self._iaas is None:
            iaas_client_conf = self.v2v_conf["pitrix"]["conf"]["iaas_client_conf"]
            self._iaas = IAASInterface(iaas_client_conf)
        return self._iaas

    @property
    def local_node(self):
        if self._node is None:
            from hyper_node import HyperNode
            self._node = HyperNode(LOCAL_NODE_ID)
        return self._node
