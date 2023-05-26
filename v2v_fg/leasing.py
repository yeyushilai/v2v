# -*- coding: utf-8 -*-

"""
Created on 2013-04-13

@author: yunify
"""
from api.common import is_system_image, update_bm_price_info, parse_duration
from api.constants import LEASE_STATUS_CREATING, EIP_BILLING_MODE_TRAFFIC,LEASE_STATUS_RECOVERING, LEASE_STATUS_RESUMING,\
                          CLUSTER_PRICE_FIELD_CLUSTER_ID, CLUSTER_PRICE_FIELD_METADATA,\
                          CLUSTER_PRICE_FIELD_CONTAINER, CLUSTER_PRICE_FIELD_RESOURCE_CLASS,\
                          CLUSTER_PRICE_FIELD_STATUS, CLUSTER_PRICE_FIELD_METADATA_CPU, CLUSTER_PRICE_FIELD_METADATA_MEMORY,\
                          CLUSTER_PRICE_FIELD_METADATA_COUNT, CLUSTER_PRICE_FIELD_METADATA_ROLE,\
                          CLUSTER_PRICE_FIELD_NODE, CLUSTER_PRICE_FIELD_METADATA_GPU, CLUSTER_PRICE_FIELD_GPU_CLASS,\
                          RESOURCE_CLASS_HIGH_PERFORMANCE,\
    CLUSTER_PRICE_FIELD_NODE_REPLICA, CLUSTER_PRICE_FIELD_STORAGE_SIZE,\
    CLUSTER_PRICE_FIELD_STORAGE_CLASS, CLUSTER_PRICE_FIELD_APP_ID, CLUSTER_PRICE_FIELD_APP_VERSION
from api.constants import (
    CLUSTER_PRICE_FIELD_METADATA_EXTRA
)

from api.constants import INSTANCE_HYPERVISOR_BM, LEASE_STATUS_ACTIVE

from db.constants import INDEXED_COLUMNS, TB_SNAPSHOT, TB_INSTANCE, \
                         TB_VOLUME, TB_IMAGE, TB_ROUTER, TB_S2_SERVER, \
                         TB_LB_EIP, TB_BANDWIDTH, TB_EIP, TB_EIP_COUNT, TB_CACHE_NODE,\
                         TB_LB_CLUSTER, TB_INSTANCE_EXTRA, TB_STORM_NODE,\
                         TB_DEDICATED_HOST_GROUP, TB_CLUSTER_NODE, TB_NFV_CLUSTER
from db.constants import (
    TB_VPC_BORDER,
    TB_VOLUME_EXTRA,
)
from utils.id_tool import (
    get_resource_type,
    RESOURCE_TYPE_CLUSTER,
    RESOURCE_TYPE_OPSBUILDER,
    RESOURCE_TYPE_VPC_BORDER,
    RESOURCE_TYPE_NFV
)
from utils.misc import get_current_time
from log.logger import logger
import api.error_code as ErrorCodes
import api.error_msg as ErrorMsg
from api.error import Error
from utils.appcenter import get_app_node_replica_policy
from fg import context


def lease(instance_owner, instance_id_list, price_info):
    pass


def unlease(instance_owner, instance_id_list, price_info):
    pass


def get_lease_infos(user_id, resource_ids):
    pass


def get_lease_info(user_id, resource_id):
    pass


def unlease_resources(table, resources, cease=0):
    """ unlease resources """
    # get resource by user
    user_resources = {}
    for resource in resources.values():
        user_id = resource['owner']
        if user_id not in user_resources:
            user_resources[user_id] = []
        resource_id = resource[INDEXED_COLUMNS[table][0]]
        user_resources[user_id].append(resource_id)

        if table == 'eip':
            # eip traffic use `eipt-xxxxxx` as resource id in billing
            user_resources[user_id].append(resource_id.replace('eip-', 'eipt-', 1))
        elif table == 'cluster':
            # cluster app service use `cla-xxxxxx` as resource id in billing
            user_resources[user_id].append(resource_id.replace('cl-', 'cla-', 1))
            user_resources[user_id].append(resource_id.replace('cl-', 'clv-', 1))

    # unlease
    for user_id, resource_ids in user_resources.items():
        if not unlease(user_id, resource_ids, cease=cease):
            logger.error("unlease resource [%s] failed" % resource_ids)
            return False
    return True


def check_resources_leasing(table, resources, ignore_creating_error=False):
    """ check if resources lease info is ready """
    # get resource by user
    user_resources = {}
    for resource in resources.values():
        user_id = resource['owner']
        if user_id not in user_resources:
            user_resources[user_id] = []
        resource_id = resource[INDEXED_COLUMNS[table][0]]
        user_resources[user_id].append(resource_id)
        if table == TB_EIP and resource['billing_mode'] == EIP_BILLING_MODE_TRAFFIC:
            user_resources[user_id].append(resource_id.replace('eip-', 'eipt-'))
    
    # check leasing
    for user_id, resource_ids in user_resources.items():
        lease_info_set = get_lease_infos(user_id, resource_ids)
        for resource_id in resource_ids:
            if resource_id not in lease_info_set:
                logger.error("get resource [%s] lease info failed" % resource_id)
                # snapshot may be created before leasing info is established, so return
                # permission denied is easy for user to understand
                if table in [TB_SNAPSHOT]:
                    return Error(ErrorCodes.PERMISSION_DENIED, 
                                 ErrorMsg.ERR_MSG_RESOURCE_LEASE_INFO_NOT_READY, resource_id)
                else:
                    if not ignore_creating_error:
                        return Error(ErrorCodes.INTERNAL_ERROR,
                                     ErrorMsg.ERR_MSG_RESOURCE_LEASE_INFO_NOT_FOUND, resource_id)

            if resource_id in lease_info_set and lease_info_set[resource_id]['status'] == LEASE_STATUS_CREATING:
                logger.error("resource [%s] lease info not ready" % resource_id)
                if not ignore_creating_error:
                    return Error(ErrorCodes.PERMISSION_DENIED,
                                 ErrorMsg.ERR_MSG_RESOURCE_LEASE_INFO_NOT_READY, resource_id)
    return resources


def update_resource_leasing(resource_id, extra=None):  
    resource_type = get_resource_type(resource_id, verbose=0)
    if resource_type == 'instance':
        ret = update_instance_leasing(resource_id, extra=extra)
    elif resource_type == 'cache':
        ret = update_cache_leasing(resource_id)
    elif resource_type == 'zookeeper':
        ret = update_zookeeper_leasing(resource_id)
    elif resource_type == 'queue':
        ret = update_queue_leasing(resource_id)
    elif resource_type == 'spark':
        ret = update_spark_leasing(resource_id)
    elif resource_type == RESOURCE_TYPE_CLUSTER:
        ret = update_cluster_leasing(resource_id)
    elif resource_type == RESOURCE_TYPE_VPC_BORDER:
        ret = update_vpc_border_leasing(resource_id)
    else:
        ret = Error(ErrorCodes.PERMISSION_DENIED, 
                                   ErrorMsg.ERR_MSG_ILLEGAL_RESOURCE_TYPE, resource_id)
        
    return ret

def check_gpu_instance(instance_id):
    pass

def get_bm_instance_type_info(instance_type_list):
    pass

def update_instance_leasing(instance_id, extra=None):
    ctx = context.instance()
    instance = ctx.zone_pg.get(TB_INSTANCE, instance_id)
    if instance is None:
        logger.error("instance [%s] not found" % (instance_id))
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND, instance_id)
    # get image
    image_id = instance['image_id']
    image = ctx.zone_pg.get(TB_IMAGE, image_id)
    if image is None:
        logger.error("image [%s] not found" % (image_id))
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND, image_id)

    instance_extra = ctx.zone_pg.get(TB_INSTANCE_EXTRA, instance_id)

    # if extra == "instance_appr":
    #     update_instance_appr_leasing([instance_id])
    #     return instance

    # check resource leasing
    ret = check_update_leasing_permission(instance, instance_id)
    if isinstance(ret, Error):
        return ret

    gpu_info = check_gpu_instance(instance_id)
    gpu = 0
    gpu_class = 0
    if gpu_info:
        gpu = gpu_info["gpu"]
        gpu_class = gpu_info["gpu_class"]

    repl = ctx.pgm.get_repl_policy(instance_id).get("conf_policy_id", "")
    # update leasing
    price_info = {'cpu': instance['vcpus_current'],
                  'memory': instance['memory_current'],
                  'image_id': image['billing_id'],
                  'image_size': image['size'],
                  'status': instance['status'],
                  'instance_class': instance['instance_class'],
                  'gpu': gpu,
                  'gpu_class': gpu_class,
                  'features': instance_extra[
                      "features"] if instance_extra else 0,
                  'repl': repl}

    # image size should be base image size
    if image['billing_id'] and image['billing_id'] != image_id:
        base_image_info = ctx.zone_pg.get(TB_IMAGE, image['billing_id'])
        if base_image_info is None:
            logger.critical(
                "image [%s] not found, correct image_size failed" % (
                image['billing_id']))
        else:
            price_info['image_size'] = base_image_info['size']

    if instance_extra:
        if instance_extra["os_disk_size"] > price_info['image_size']:
            # when os disk is resized, billing extra price
            price_info["os_disk_size"] = instance_extra["os_disk_size"]

        if instance_extra["hypervisor"] == INSTANCE_HYPERVISOR_BM:
            instance_type = instance.get("instance_type", None)
            instance_type_info = get_bm_instance_type_info([instance_type])
            if not instance_type_info:
                return Error(ErrorCodes.INTERNAL_ERROR,
                             ErrorMsg.ERR_MSG_ILLEGAL_INSTANCE_TYPE,
                             instance_type)
            update_bm_price_info(price_info, instance_type_info)

    if not lease(instance['owner'], [instance_id], price_info):
        logger.error(
            "update lease price for instance [%s] failed" % instance_id)
        return Error(ErrorCodes.INTERNAL_ERROR,
                     ErrorMsg.ERR_MSG_LEASE_FAILED, instance_id)

    # update_instance_appr_leasing([instance_id])

    return instance


def update_zookeeper_leasing(zookeeper_id):
    ctx = context.instance()
    zookeeper = ctx.pgm.get_zookeeper(zookeeper_id, extras=[])
    if not zookeeper:
        logger.error("Zookeeper [%s] not found")
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND,
                     zookeeper_id)

    ret = check_update_leasing_permission(zookeeper, zookeeper_id)
    if isinstance(ret, Error):
        return ret

    price_info = dict(zookeeper_id=zookeeper_id,
                      zookeeper_version=zookeeper["zookeeper_version"],
                      zookeeper_type=zookeeper["zookeeper_type"],
                      node_count=zookeeper["cluster_size"],
                      storage_size=zookeeper["storage_size"],
                      status=zookeeper["status"],
                      resource_class=zookeeper['resource_class'],
                      repl=zookeeper.get('repl',""))
    if not lease(zookeeper["owner"], [zookeeper_id], price_info):
        return Error(ErrorCodes.INTERNAL_ERROR,
                     ErrorMsg.ERR_MSG_LEASE_FAILED,
                     zookeeper_id)

    return zookeeper


def check_update_leasing_permission(resource, resource_id):
    """ check if resource leasing is ready before UpdateResourceLeasing """
    ctx = context.instance()
    allowed_update_resource_leasing = ctx.resource_limits[ctx.zone_id].get('update_resource_leasing', 0)
    
    # check if lease info ready
    lease_info = get_lease_info(resource['owner'], resource_id)
    if lease_info is None:
        if allowed_update_resource_leasing:
            return None
        logger.error("get resource [%s] lease info failed." % (resource_id))
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_LEASE_INFO_NOT_FOUND, resource_id)
    elif lease_info['status'] in [LEASE_STATUS_CREATING, LEASE_STATUS_RECOVERING, LEASE_STATUS_RESUMING]:
        logger.error("resource [%s] lease info not ready." % (resource_id))
        return Error(ErrorCodes.PERMISSION_DENIED,
                     ErrorMsg.ERR_MSG_RESOURCE_LEASE_INFO_NOT_READY, resource_id)
    elif lease_info['status'] != LEASE_STATUS_ACTIVE:
        logger.error("resource [%s] lease info not active." % (resource_id))
        return Error(ErrorCodes.PERMISSION_DENIED,
                     ErrorMsg.ERR_MSG_RESOURCE_LEASE_INFO_NOT_ACTIVE, resource_id)
    return lease_info


def update_cache_leasing(cache_id):
    ctx = context.instance()
    cache = ctx.pgm.get_cache(cache_id, [TB_CACHE_NODE])
    if cache is None:
        logger.error("cache [%s] not found" % (cache_id))
        return Error(ErrorCodes.RESOURCE_NOT_FOUND, 
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND, cache_id)
         
    # check resource leasing
    ret = check_update_leasing_permission(cache, cache_id)
    if isinstance(ret, Error):
        return ret
    
    # update leasing
    price_info = {'cache_type': cache['cache_type'],
                  'cache_size': cache['cache_size'],
                  'node_count': len(cache['nodes']),
                  'status': cache['status'],
                  'cpu': cache['cpu'],
                  'memory': cache['memory'],
                  'cache_class': cache['cache_class']}
    if not lease(cache['owner'], [cache_id], price_info):
        logger.error("update lease price for cache [%s] failed" % cache_id)
        return Error(ErrorCodes.INTERNAL_ERROR, 
                     ErrorMsg.ERR_MSG_LEASE_FAILED, cache_id)  
        
    return cache


def update_queue_leasing(queue_id):
    ctx = context.instance()
    queue = ctx.pgm.get_queue(queue_id, extras=[])
    if not queue:
        logger.error("Queue [%s] not found")
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND,
                     queue_id)

    ret = check_update_leasing_permission(queue, queue_id)
    if isinstance(ret, Error):
        return ret

    price_info = dict(queue_id=queue_id,
                      queue_type=queue["queue_type"],
                      node_count=queue["cluster_size"],
                      storage_size=queue["storage_size"],
                      status=queue["status"],
                      resource_class=queue['resource_class'],
                      repl=queue.get('repl',""))
    if not lease(queue["owner"], [queue_id], price_info):
        return Error(ErrorCodes.INTERNAL_ERROR,
                     ErrorMsg.ERR_MSG_LEASE_FAILED,
                     queue_id)

    return queue


def update_spark_leasing(spark_id):
    ctx = context.instance()
    spark = ctx.pgm.get_spark(spark_id, extras=[])
    if not spark:
        logger.error("Spark [%s] not found")
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND,
                     spark_id)

    ret = check_update_leasing_permission(spark, spark_id)
    if isinstance(ret, Error):
        return ret

    ctx = context.instance()
    worker_cpu = ctx.resource_limits[ctx.zone_id]["spark_types"][spark["spark_type"]]["cpu"]
    worker_memory = ctx.resource_limits[ctx.zone_id]["spark_types"][spark["spark_type"]]["memory"]
    spark_master_cpu = ctx.resource_limits[ctx.zone_id]["spark_types"][spark["spark_master_type"]]["cpu"]
    spark_master_memory = ctx.resource_limits[ctx.zone_id]["spark_types"][spark["spark_master_type"]]["memory"]
    

    price_info = dict(spark_id=spark_id,
                      cpu=worker_cpu,
                      memory=worker_memory,
                      node_count=spark["cluster_size"],
                      storage_size=spark["storage_size"],
                      sk_storage=spark["spark_master_storage_size"],
                      sk_cpu=spark_master_cpu,
                      sk_memory=spark_master_memory,
                      status=spark["status"],
                      resource_class=spark['resource_class'],
                      repl=spark.get('repl',""))
    if spark["enable_hdfs"] == 1:
        hadoop_master_storage_size =  spark["hadoop_master_storage_size"]
        hadoop_master_cpu = ctx.resource_limits[ctx.zone_id]["spark_types"][spark["hadoop_master_type"]]["cpu"]
        hadoop_master_memory = ctx.resource_limits[ctx.zone_id]["spark_types"][spark["hadoop_master_type"]]["memory"]
        price_info.update({'hdp_storage' : hadoop_master_storage_size,
                           'hdp_cpu':hadoop_master_cpu,
                           'hdp_memory':hadoop_master_memory,
                           })
    if not lease(spark["owner"], [spark_id], price_info):
        return Error(ErrorCodes.INTERNAL_ERROR,
                     ErrorMsg.ERR_MSG_LEASE_FAILED,
                     spark_id)

    return spark


def update_cluster_leasing(cluster_id):
    ctx = context.instance()
    cluster = ctx.pgm.get_cluster(cluster_id, extras=[TB_CLUSTER_NODE])
    if not cluster:
        logger.error("Cluster [%s] not found", cluster_id)
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND,
                     cluster_id)

    ret = check_update_leasing_permission(cluster, cluster_id)
    if isinstance(ret, Error):
        return ret

    duration, charge_mode = None, None
    if ret:
        duration = ret['contract']['duration']
        duration = parse_duration(duration)
        charge_mode = ret['contract']['charge_mode']
    
    billing_metadata = {}
    nodes_billing_metadata = []
    nodes = cluster["nodes"]
    first_node = nodes.values()[0]
    if first_node["role"]:
        role_nodes = {}
        for node in nodes.values(): # rearrange the nodes based on role and get the storage as well
            if node["role"] not in role_nodes.keys():
                role_nodes[node["role"]] = [node]
            else:
                role_nodes[node["role"]].append(node)
        for role, node_list in role_nodes.items():
            node = node_list[0]
            billing = {
                       CLUSTER_PRICE_FIELD_METADATA_ROLE    : role, 
                       CLUSTER_PRICE_FIELD_METADATA_CPU     : node["cpu"], 
                       CLUSTER_PRICE_FIELD_METADATA_MEMORY  : node["memory"],
                       CLUSTER_PRICE_FIELD_METADATA_GPU     : node["gpu"],
                       CLUSTER_PRICE_FIELD_GPU_CLASS        : node["gpu_class"],
                       CLUSTER_PRICE_FIELD_CONTAINER        : node["hypervisor"],
                       CLUSTER_PRICE_FIELD_RESOURCE_CLASS   : node["resource_class"],    
                       CLUSTER_PRICE_FIELD_METADATA_COUNT   : len(node_list),
                       CLUSTER_PRICE_FIELD_NODE_REPLICA     : get_app_node_replica_policy(node["repl"], 
                                                                                          node["single_node_repl"],
                                                                                          len(node_list))
                      }
            if node["storage_size"] and node["storage_size"] > 0:
                billing[CLUSTER_PRICE_FIELD_STORAGE_SIZE] = node["storage_size"]
                billing[CLUSTER_PRICE_FIELD_STORAGE_CLASS] = node["volume_type"]
            instance_type = node.get("instance_type")
            if instance_type:
                instance_type_info = get_bm_instance_type_info([instance_type])
                if instance_type_info:
                    billing[CLUSTER_PRICE_FIELD_METADATA_EXTRA] = instance_type_info["extra_info"]
            nodes_billing_metadata.append(billing)
    else: # no role based
        billing = {
                   CLUSTER_PRICE_FIELD_METADATA_CPU     : first_node["cpu"], 
                   CLUSTER_PRICE_FIELD_METADATA_MEMORY  : first_node["memory"],
                   CLUSTER_PRICE_FIELD_METADATA_GPU     : first_node["gpu"],
                   CLUSTER_PRICE_FIELD_GPU_CLASS        : first_node["gpu_class"],
                   CLUSTER_PRICE_FIELD_CONTAINER        : first_node["hypervisor"],
                   CLUSTER_PRICE_FIELD_RESOURCE_CLASS   : first_node["resource_class"],     
                   CLUSTER_PRICE_FIELD_METADATA_COUNT   : cluster["cluster_size"],
                   CLUSTER_PRICE_FIELD_NODE_REPLICA     : get_app_node_replica_policy(first_node["repl"], 
                                                                                      first_node["single_node_repl"],
                                                                                      cluster["cluster_size"])
                  }
        if first_node["storage_size"] and first_node["storage_size"] > 0:
            billing[CLUSTER_PRICE_FIELD_STORAGE_SIZE] = first_node["storage_size"]
            billing[CLUSTER_PRICE_FIELD_STORAGE_CLASS] = first_node["volume_type"]
        instance_type = first_node.get("instance_type")
        if instance_type:
            instance_type_info = get_bm_instance_type_info([instance_type])
            if instance_type_info:
                billing[CLUSTER_PRICE_FIELD_METADATA_EXTRA] = instance_type_info["extra_info"]
        nodes_billing_metadata.append(billing)
        
    # compose billing_metadata
    billing_metadata[CLUSTER_PRICE_FIELD_NODE] = nodes_billing_metadata
                    
    price_info = {CLUSTER_PRICE_FIELD_CLUSTER_ID     : cluster_id,
                  CLUSTER_PRICE_FIELD_APP_ID         : cluster["app_id"],
                  CLUSTER_PRICE_FIELD_APP_VERSION    : cluster["app_version"],
                  CLUSTER_PRICE_FIELD_METADATA       : billing_metadata,                   
                  CLUSTER_PRICE_FIELD_STATUS         : cluster["status"]
                 }

    if not lease(cluster["owner"], [cluster_id], price_info, duration, charge_mode):
        return Error(ErrorCodes.INTERNAL_ERROR,
                     ErrorMsg.ERR_MSG_LEASE_FAILED,
                     cluster_id)

    return cluster


def update_vpc_border_leasing(vpc_border_id):
    ctx = context.instance()
    vpc_border = ctx.zone_pg.get(TB_VPC_BORDER, vpc_border_id)

    if not vpc_border:
        logger.error("Get vpc border [%s] failed", vpc_border_id)
        return Error(ErrorCodes.RESOURCE_NOT_FOUND,
                     ErrorMsg.ERR_MSG_RESOURCE_NOT_FOUND,
                     vpc_border_id)

    # check resource leasing
    ret = check_update_leasing_permission(vpc_border, vpc_border_id)
    if isinstance(ret, Error):
        return ret

    # update leasing
    price_info = {'status': vpc_border['status'],
                  'border_type': vpc_border['border_type']}
    if not lease(vpc_border["owner"], [vpc_border_id], price_info):
        logger.error("update lease price for vpc border [%s] failed",
                     vpc_border_id)
        return Error(ErrorCodes.INTERNAL_ERROR,
                     ErrorMsg.ERR_MSG_LEASE_FAILED,
                     vpc_border_id)

    return vpc_border
