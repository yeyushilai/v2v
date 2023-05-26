# -*- coding: utf-8 -*-

"""功能：API接口层面的ZK操作 """

import os

from log.logger import logger
from utils.global_conf import get_zk
from constants.zk import V2V_WORKER_ZK_BASE_DIR


class ZKInterface(object):

    def __init__(self):
        self.zk_client = get_zk()

    def delete_hyper_node(self, hyper_node_id):
        """从ZK中删除hyper节点"""
        v2v_worker_path = os.path.join(V2V_WORKER_ZK_BASE_DIR, hyper_node_id)
        try:
            logger.info("delete node from zk ready, hyper node id: "
                        "{hyper_node_id}, worker worker path: {v2v_worker_path}"
                        .format(hyper_node_id=hyper_node_id,
                                v2v_worker_path=v2v_worker_path))
            self.zk_client.delete(v2v_worker_path)
        except Exception as e:
            log_msg = "delete node from zk failed, hyper node id: " \
                      "{hyper_node_id}, worker worker path: {v2v_worker_path}, " \
                      "error reason: {error_reason}" \
                .format(hyper_node_id=hyper_node_id,
                        v2v_worker_path=v2v_worker_path,
                        error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

    def register_hyper_node(self, hyper_node_id):
        """注册hyper节点到ZK"""
        v2v_worker_path = os.path.join(V2V_WORKER_ZK_BASE_DIR, hyper_node_id)
        try:
            logger.info("register hyper node to zk ready, hyper node id: "
                        "{hyper_node_id}, worker worker path: {v2v_worker_path}"
                        .format(hyper_node_id=hyper_node_id,
                                v2v_worker_path=v2v_worker_path))
            self.zk_client.create(V2V_WORKER_ZK_BASE_DIR,
                                  V2V_WORKER_ZK_BASE_DIR.replace("/", ""))
            self.zk_client.create_ephemeral(v2v_worker_path, hyper_node_id)
        except Exception as e:
            log_msg = "hyper node register to zk failed, hyper node id: " \
                      "{hyper_node_id}, worker worker path: {v2v_worker_path}, " \
                      "error reason: {error_reason}" \
                .format(hyper_node_id=hyper_node_id,
                        v2v_worker_path=v2v_worker_path,
                        error_reason=str(e))
            logger.error(log_msg)
            raise Exception(log_msg)

    def check_hyper_node(self, hyper_node_id):
        """检查节点在ZK上是否注册成功
         注册成功返回True，注册失败或者请求异常返回抛出异常
        """
        log_msg = "check whether register hyper node to zk success start, hyper " \
                  "node id: {hyper_node_id}, error reason: {error_reason}"
        try:
            logger.info(
                "check whether register hyper node to zk success ready, "
                "hyper node id: {hyper_node_id}"
                "".format(hyper_node_id=hyper_node_id))
            content = self.zk_client.get_children(V2V_WORKER_ZK_BASE_DIR)

        except Exception as e:
            log_msg = log_msg.format(hyper_node_id=hyper_node_id,
                                     error_reason=e)
            logger.error(log_msg)
            raise Exception(log_msg)

        else:
            if content is None:
                log_msg = log_msg.format(hyper_node_id=hyper_node_id,
                                         error_reason="worker dir is none")
                logger.error(log_msg)
                raise Exception(log_msg)
            logger.info("register node content: %s" % content)
            if hyper_node_id not in content:
                log_msg = log_msg.format(hyper_node_id=hyper_node_id,
                                         error_reason="hyper node not in worker dir")
                logger.error(log_msg)
                raise Exception(log_msg)
            return True
