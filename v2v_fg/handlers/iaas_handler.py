# -*- coding: utf-8 -*-

from log.logger import logger
from api.constants import (
    # instance_class
    INSTANCE_CLASS_SAN_CONTAINER,
    INSTANCE_CLASS_HIGH_CAPACITY_SAN,

    # volume_type
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED,
    VOLUME_TYPE_HIGH_CAPACITY_SAN,
)
from db.constants import (
    TB_HYPER_NODE,
    TB_HYPERNODE_PLG,
    TB_PLACE_GROUP_RULE
)

from fg import context
from fg.constants import (
    # action
    ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES,
    ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES_PG_RULE,

    # zk
    V2V_ZK_HYPER_PATH
)
from fg.return_tools import return_success
from fg.uutils.zk.interface import discover_v2v_worker


CTX = context.instance()


def handle_describe_iaas_hyper_nodes(req):
    """获取青云平台中部署了V2V迁移服务的hyper节点列表信息"""
    logger.debug('handle get v2v hyper nodes start, {}'.format(req))
    offset = req.get("offset")
    limit = req.get("limit")
    search_word = req.get("search_word")
    dst_zone_id = req.get("dst_zone_id")

    ret = {
        "bot_set": [],
        "total_count": 0
    }
    bots = discover_v2v_worker()
    if not bots:
        logger.error("discover v2v worker result: [%s]" % bots)
    if bots and len(bots) > 0:
        ret = CTX.iaas.describe_bots(bots=bots, offset=offset, limit=limit,
                                     search_word=search_word,
                                     zone=dst_zone_id)
    else:
        logger.error("get v2v hyper fail, path: {}".format(V2V_ZK_HYPER_PATH))

    return return_success(req, None, **ret)


def handle_describe_iaas_hyper_nodes_pg_rule(req):
    """获取青云平台中部署了V2V迁移服务的hyper节点的安置组策略信息"""
    logger.debug('handle get v2v hyper nodes pg rule start, {}'.format(req))
    hyper_node_ids = req.get("hyper_node_ids")

    # 获取HYPER节点关联的所有安置组
    place_group_list = CTX.zone_pg.base_get(table=TB_HYPERNODE_PLG,
                                            condition={
        "hyper_node_id": hyper_node_ids})
    place_group_ids = [plg["place_group_id"] for plg in place_group_list]
    place_group_ids.append("")

    # 获取安置组对应的所有的安置规则
    place_group_rule_list = CTX.zone_pg.base_get(table=TB_PLACE_GROUP_RULE,
                                                 condition={"place_group_id": place_group_ids})
    assert place_group_rule_list is not []

    instance_class = []
    volume_type = []
    for rule in place_group_rule_list:
        resource_info = rule.get("resource_info")
        ins = None
        vol = None
        if resource_info.startswith("instance_class_"):
            _, instance_enum = resource_info.split("instance_class_")
            if instance_enum and instance_enum.isdigit():
                ins = int(instance_enum)
            else:
                print instance_enum
            if isinstance(ins, int) and ins not in instance_class:
                instance_class.append(ins)
        elif resource_info.startswith("volume_type_"):
            _, volume_enum = resource_info.split("volume_type_")
            if volume_enum and volume_enum.isdigit():
                vol = int(volume_enum)
            else:
                print volume_enum
            if isinstance(vol, int) and vol not in volume_type:
                volume_type.append(vol)
        else:
            continue

    # 如果是sanc环境，需要单独判断
    hyper_nodes = CTX.zone_pg.base_get(table=TB_HYPER_NODE, condition={
        "hyper_node_id": hyper_node_ids})
    if "sanc" in [hyper_node["container_mode"] for hyper_node in hyper_nodes]:
        instance_class.append(INSTANCE_CLASS_HIGH_CAPACITY_SAN)
        volume_type.append(VOLUME_TYPE_HIGH_CAPACITY_SAN)
    else:
        if VOLUME_TYPE_HIGH_PERFORMANCE_SHARED in volume_type:
            volume_type.remove(VOLUME_TYPE_HIGH_PERFORMANCE_SHARED)
        if INSTANCE_CLASS_SAN_CONTAINER in instance_class:
            instance_class.remove(INSTANCE_CLASS_SAN_CONTAINER)

    if len(instance_class) == 0:
        instance_class.append(0)
    if len(volume_type) == 0:
        volume_type.append(0)

    instance_class.sort()
    volume_type.sort()
    return return_success(req,
                          None,
                          datas={"instance_class": instance_class,
                                 "volume_type": volume_type})


HANDLER_MAP = {
    ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES: handle_describe_iaas_hyper_nodes,
    ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES_PG_RULE: handle_describe_iaas_hyper_nodes_pg_rule

}
