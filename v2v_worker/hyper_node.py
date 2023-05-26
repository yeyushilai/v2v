# -*- coding: utf-8 -*-

"""功能：hyper节点模块"""

import socket

from log.logger import logger
from context import WorkerContext
from api.constants import (
    # 虚拟机类型6和7
    INSTANCE_CLASS_SAN_CONTAINER,
    INSTANCE_CLASS_HIGH_CAPACITY_SAN,

    # 硬盘类型5和6
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED,
    VOLUME_TYPE_HIGH_CAPACITY_SAN,

)
from constants.pg import (
    DSTINSTANCECLASSPREFIX,
    DSTVOLUMETYPEPREFIX
)
from constants.iaas import HyperContainerMode


CTX = WorkerContext()


class HyperNode(object):
    """Hyper节点类"""

    def __init__(self, node_id):
        self._node_id = node_id
        self._info = dict()

    @property
    def info(self):
        if not self._info:
            self._info = CTX.zone_pg.query_node(self.node_id)
        return self._info

    @info.setter
    def info(self, value):
        """更新内存中全部数据"""
        self.info.update(value)

    @property
    def node_id(self):
        return self._node_id

    @property
    def node_ip(self):
        return socket.gethostbyname(self._node_id)

    def update(self, value):
        """更新hyper_node数据表记录"""
        CTX.zone_pg.update_node(self.node_id, value)

    @property
    def container_mode(self):
        return self.info["container_mode"]

    @property
    def zone_id(self):
        return self.info["zone_id"]

    def query_support_resource(self):
        node_plg_list = CTX.zone_pg.list_node_plg(self.node_id)
        plg_id_list = [node_plg["place_group_id"] for node_plg in node_plg_list]
        plg_id_list.append("")

        pg_rule_list = CTX.zone_pg.list_place_group_rule(place_group_id=plg_id_list)

        # 过滤类型，切片取值
        pg_instance_type_rule_list = filter(lambda x: x["resource_info"].startswith(DSTINSTANCECLASSPREFIX), pg_rule_list)
        pg_volume_type_rule_list = filter(lambda x: x["resource_info"].startswith(DSTVOLUMETYPEPREFIX), pg_rule_list)
        instance_type_list = list({int(pg_rule["resource_info"].split("_")[-1]) for pg_rule in pg_instance_type_rule_list})
        volume_type_list = list({int(pg_rule["resource_info"].split("_")[-1]) for pg_rule in pg_volume_type_rule_list})

        # SANC环境特殊判断
        if self.container_mode == HyperContainerMode.SANC.value:
            instance_type_list.append(INSTANCE_CLASS_HIGH_CAPACITY_SAN)
            volume_type_list.append(VOLUME_TYPE_HIGH_CAPACITY_SAN)
        else:
            if INSTANCE_CLASS_SAN_CONTAINER in instance_type_list:
                instance_type_list.remove(INSTANCE_CLASS_SAN_CONTAINER)
            if VOLUME_TYPE_HIGH_PERFORMANCE_SHARED in volume_type_list:
                volume_type_list.remove(VOLUME_TYPE_HIGH_PERFORMANCE_SHARED)

        logger.info("node({node_id}) support resource as follow, support "
                    "instance type list: {instance_type_list}, support volume "
                    "type list: {volume_type_list}"
                    "".format(node_id=self.node_id,
                              instance_type_list=instance_type_list,
                              volume_type_list=volume_type_list))

        return dict(instance_type=instance_type_list,
                    volume_type=volume_type_list)
