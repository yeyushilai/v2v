# -*- coding: utf-8 -*-

from log.logger import logger
from qingcloud.iaas import APIConnection
from api.constants import (
    # 虚拟机相关动作
    ACTION_UPDATE_RESOURCE_LEASING,
    ACTION_RUN_INSTANCES,
    ACTION_DESCRIBE_INSTANCES,
    ACTION_RESTART_INSTANCES,
    ACTION_START_INSTANCES,
    ACTION_STOP_INSTANCES,

    # 卷相关动作
    ACTION_CREATE_VOLUMES,
    ACTION_ATTACH_VOLUMES,
    ACTION_DESCRIBE_VOLUMES,

    # 配额相关动作
    ACTION_DESCRIBE_QUOTAS,
    ACTION_UPDATE_QUOTAS,

    # hyper相关动作
    ACTION_DESCRIBE_BOTS
)

from constants.common import LOCAL_NODE_ID
from constants.iaas import (
    INSTANCE_CPU_TYPE,
    INSTANCE_MEMORY_TYPE
)


class IAASInterface(object):
    def __init__(self, iaas_client_conf):
        if "debug" not in iaas_client_conf.keys():
            iaas_client_conf["debug"] = False
        self.iaas_client = APIConnection(**iaas_client_conf)

    def update_resource_leasing(self, resource_id):
        """更新资源租赁计费信息"""
        action = ACTION_UPDATE_RESOURCE_LEASING
        body = dict(resource=resource_id)

        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'update resource leasing failed, body: {body}, error ' \
                      'reason: {error}'.format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info(
                'update resource leasing, body: {body}, res: {res}'
                    .format(body=body,
                            res=res))
            if res['ret_code'] != 0:
                log_msg = 'update resource leasing failed, body({body}), ' \
                          'res({res})'.format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            return res

    def run_instance(self, image_id, instance_class, cpu, memory,
                     target_user, os_disk_size, count=1, login_mode='passwd',
                     login_passwd='Zhu88jie', instance_name=None, zone=None,
                     vxnet_info=None, hyper_node_id=LOCAL_NODE_ID):
        """创建虚拟机"""
        action = ACTION_RUN_INSTANCES
        if cpu not in INSTANCE_CPU_TYPE:
            log_msg = "cpu core({cpu}) not in cpu type list({cpu_type})" \
                .format(cpu=cpu, cpu_type=INSTANCE_CPU_TYPE)
            logger.exception(log_msg)
            raise Exception(log_msg)
        if memory not in INSTANCE_MEMORY_TYPE:
            log_msg = "memory size({memory}) not in memory type " \
                      "list({memory_type})".format(memory=memory,
                                                   memory_type=INSTANCE_MEMORY_TYPE)
            logger.exception(log_msg)
            raise Exception(log_msg)

        body = dict(
            image_id=image_id,
            instance_class=instance_class,
            cpu=cpu,
            memory=memory,
            target_user=target_user,
            count=count,
            login_mode=login_mode,
            login_passwd=login_passwd,
            os_disk_size=os_disk_size)

        body.setdefault("zone", zone or self.iaas_client.conn.zone)

        if hyper_node_id:
            body["hyper_node_id"] = hyper_node_id
        if instance_name:
            body["instance_name"] = instance_name
        if vxnet_info:
            body["vxnets"] = [vxnet_info, ]

        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'run instance failed, action: {action}, body: {body}, ' \
                      'error reason: {error}' \
                      ''.format(body=body, action=action, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('run instance, action: {action}, body: {body}, res: '
                        '{res}'.format(body=body, action=action, res=res))
            if res['ret_code'] != 0:
                log_msg = 'run instance failed, body: {body}, res: {res}' \
                    .format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            return res

    def describe_instance(self, instance_id, zone=None):
        """展示虚拟机信息"""
        action = ACTION_DESCRIBE_INSTANCES
        body = dict(instances=[instance_id.strip(), ])
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'describe instance failed, body: {body}, error reason: ' \
                      '{error}' \
                .format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('describe instance info, body: {body}, res: {res}'
                        .format(body=body, res=res))
            if res['ret_code'] != 0 and res['total_count'] != 1:
                log_msg = 'describe instance info failed, body: {body}), ' \
                          'res:{res}'.format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            instance_config = res['instance_set'][0]
            return instance_config

    def restart_instance(self, instance_id, zone=None):
        """重启虚拟机"""
        action = ACTION_RESTART_INSTANCES
        body = dict(instances=[instance_id, ])
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        res = self.iaas_client.send_request(action=action, body=body)
        logger.info(
            'restart instance, body: {body}, res: {res}'.format(body=body,
                                                                res=res))
        if res['ret_code'] != 0:
            log_msg = 'restart instance failed, body: {body}), ' \
                      'res:{res}'.format(body=body, res=res)
            logger.exception(log_msg)
            raise Exception(log_msg)
        return res

    def start_instance(self, instance_id, zone=None):
        """启动虚拟机"""
        action = ACTION_START_INSTANCES
        body = dict(instances=[instance_id, ])
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        res = self.iaas_client.send_request(action=action, body=body)
        logger.info(
            'start instance, body: {body}, res: {res}'.format(body=body,
                                                              res=res))
        if res['ret_code'] != 0:
            log_msg = 'start instance failed, body: {body}), ' \
                      'res:{res}'.format(body=body, res=res)
            logger.exception(log_msg)
            raise Exception(log_msg)
        return res

    def stop_instance(self, instance_id, force=0, zone=None):
        """关闭虚拟机"""
        action = ACTION_STOP_INSTANCES
        body = dict(instances=[instance_id, ], force=force)
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        res = self.iaas_client.send_request(action=action, body=body)
        logger.info(
            'stop instance, body: {body}, res: {res}'.format(body=body,
                                                             res=res))
        if res['ret_code'] != 0:
            log_msg = 'stop instance failed, body: {body}), ' \
                      'res:{res}'.format(body=body, res=res)
            logger.exception(log_msg)
            raise Exception(log_msg)
        return res

    def create_volume(self, volume_name, volume_type, size, target_user,
                      hyper_node_id=LOCAL_NODE_ID, count=1, zone=None):
        """创建硬盘"""
        action = ACTION_CREATE_VOLUMES
        body = dict(
            volume_type=volume_type,
            volume_name=volume_name,
            size=size,
            target_user=target_user,
            count=count
        )
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        if hyper_node_id:
            body["hyper_node_id"] = hyper_node_id
        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'create volume failed, body: {body}, error reason: ' \
                      '{error}' \
                .format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('create volume, body: {body}, res: {res}'
                        .format(body=body, res=res))
            if res['ret_code'] != 0:
                log_msg = 'create volume failed, body: {body}, res: {res}' \
                    .format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            return res

    def attach_volumes(self, instance_id, volume_id_list, zone=None):
        """加载硬盘"""
        action = ACTION_ATTACH_VOLUMES
        body = dict(instance=instance_id, volumes=volume_id_list)
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'attach volumes failed, body: {body}, error reason: {error}'
            log_msg = log_msg.format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('attach volumes, body: {body}, res: {res}'
                        .format(body=body, res=res))
            if res['ret_code'] != 0:
                log_msg = 'attach volumes failed, body: {body}, res: {res}' \
                    .format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            return res

    def describe_volume(self, volume_id, instance_id=None, zone=None):
        """查询硬盘信息"""
        action = ACTION_DESCRIBE_VOLUMES
        body = dict(volumes=[volume_id.strip(), ])
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        if instance_id:
            body["instance_id"] = instance_id
        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'describe volume failed, body: {body}, error reason: ' \
                      '{error}'.format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('describe volume info, body: {body}, res: {res}'
                        .format(body=body, res=res))
            if res['ret_code'] != 0 and res['total_count'] != 1:
                log_msg = 'describe volume info failed, body: {body}), ' \
                          'res:{res}'.format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            volume_config = res['volume_set'][0]
            return volume_config

    def describe_quotas(self, user_id_list, limit=20, offset=0, zone=None):
        """查询配额信息"""
        action = ACTION_DESCRIBE_QUOTAS
        body = dict(users=user_id_list, limit=limit, offset=offset)
        body.setdefault("zone", zone or self.iaas_client)
        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'describe quotas failed, body: {body}, error reason: {error}'
            log_msg = log_msg.format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('describe quotas, body: {body}, res: {res}'
                        .format(body=body, res=res))
            if res and res["ret_code"] != 0:
                log_msg = "describe quotas failed, body: {body}, res: {res}" \
                    .format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            return res

    def update_quotas(self, params, zone=None):
        """更新配额信息"""
        action = ACTION_UPDATE_QUOTAS
        params.setdefault("zone", zone)
        try:
            res = self.iaas_client.send_request(action=action, body=params)
        except Exception as e:
            log_msg = 'update quotas failed, body: {body}, error reason: {error}'
            log_msg = log_msg.format(body=params, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('update quotas, body: {body}, res: {res}'
                        .format(body=params, res=res))
            if res and res["ret_code"] != 0:
                log_msg = "update quotas failed, body: {body}, res: {res}" \
                    .format(body=params, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            return res

    def describe_bots(self, hyper_ids, zone=None):
        """查询HYPER信息"""
        action = ACTION_DESCRIBE_BOTS
        body = dict(bots=hyper_ids)
        body.setdefault("zone", zone or self.iaas_client.conn.zone)
        try:
            res = self.iaas_client.send_request(action=action, body=body)
        except Exception as e:
            log_msg = 'describe bots failed, body: {body}, error reason: {error}'
            log_msg = log_msg.format(body=body, error=str(e))
            logger.exception(log_msg)
            raise Exception(log_msg)
        else:
            logger.info('describe bots, body: {body}, res: {res}'
                        .format(body=body, res=res))
            if res and res["ret_code"] != 0:
                log_msg = "describe bots failed, body: {body}, res: {res}" \
                    .format(body=body, res=res)
                logger.exception(log_msg)
                raise Exception(log_msg)
            bot_config = res["bot_set"][0]
            return bot_config
