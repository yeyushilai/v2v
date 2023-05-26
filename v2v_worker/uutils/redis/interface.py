# -*- coding: utf-8 -*-

from constants.redis import (
    REDIS_CONF_NAME_V2V,
    REDIS_KEY_PREFIX,
    REDIS_KEY_SUFFIX_AUTO_NODE
)
from utils.global_conf import get_redis


class V2VRedisInterface(object):

    def __init__(self, redis_conf_name_v2v=REDIS_CONF_NAME_V2V):
        self.redis_client = get_redis(redis_conf_name_v2v)

    def set_define_node_task(self, hyper_node_id, task_id):
        key = REDIS_KEY_PREFIX + hyper_node_id
        return self.redis_client.rpush(key, task_id)

    def set_auto_node_task(self, task_id):
        key = REDIS_KEY_PREFIX + REDIS_KEY_SUFFIX_AUTO_NODE
        return self.redis_client.rpush(key, task_id)

    def get_define_node_task(self, hyper_node_id, start=0, end=-1):
        key = REDIS_KEY_PREFIX + hyper_node_id
        return self.redis_client.lrange(key, start, end)

    def get_auto_node_task(self, start=0, end=-1):
        key = REDIS_KEY_PREFIX + REDIS_KEY_SUFFIX_AUTO_NODE
        return self.redis_client.lrange(key, start, end)

    def remove_define_node_define_task(self, hyper_node_id, task_id):
        key = REDIS_KEY_PREFIX + hyper_node_id
        return self.redis_client.lrem(key, 0, task_id)

    def remove_auto_node_define_task(self, task_id):
        key = REDIS_KEY_PREFIX + REDIS_KEY_SUFFIX_AUTO_NODE
        return self.redis_client.lrem(key, 0, task_id)

    def delete_define_node(self, hyper_node_id):
        key = REDIS_KEY_PREFIX + hyper_node_id
        self.redis_client.delete(key)

    def delete_auto_node(self):
        key = REDIS_KEY_PREFIX + REDIS_KEY_SUFFIX_AUTO_NODE
        self.redis_client.delete(key)
