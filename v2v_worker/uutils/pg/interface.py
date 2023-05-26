# -*- coding: utf-8 -*-

"""功能：API接口层面的SQL操作"""

import json
from copy import deepcopy

from log.logger import logger
from utils.global_conf import get_pg
from utils.misc import get_current_time
from db.constants import (
    # db
    DB_V2V,
    DB_ZONE,
    
    # table
    TB_V2V_SRC_PLATFORM,
    TB_V2V_VM,
    TB_V2V_MIGRATE_TASK,
    TB_IMAGE,
    TB_JOB,
    TB_HYPER_NODE,
    TB_HYPERNODE_PLG,
    TB_PLACE_GROUP_RULE
)

from constants.pg import (
    MIN_CONNECT,
    MAX_CONNECT
)


class PGInterface(object):
    def __init__(self, db_name, min_connect=MIN_CONNECT, max_connect=MAX_CONNECT):
        self.db_name = db_name
        self.min_connect = min_connect
        self.max_connect = max_connect
        self.client_delegator = self.gen_client_delegator()

    def gen_client_delegator(self):
        return get_pg(self.db_name, self.min_connect, self.max_connect)


class V2VPGInterface(PGInterface):
    db_name = DB_V2V
    table_src_platform = TB_V2V_SRC_PLATFORM
    table_vm = TB_V2V_VM
    table_migrate_task = TB_V2V_MIGRATE_TASK

    max_query_count = 1000

    def __init__(self, min_connect=0, max_connect=1000):
        super(V2VPGInterface, self).__init__(self.db_name,
                                             min_connect,
                                             max_connect)

    ###########################################################################
    def create_vm(self, vm_config):
        vm_config_copy = deepcopy(vm_config)
        if isinstance(vm_config_copy["src_vm_net"], list):
            vm_config_copy["src_vm_net"] = json.dumps(
                vm_config_copy["src_vm_net"])
        if isinstance(vm_config_copy["src_vm_disk"], list):
            vm_config_copy["src_vm_disk"] = json.dumps(
                vm_config_copy["src_vm_disk"])
        if isinstance(vm_config_copy["dst_vm_disk"], list):
            vm_config_copy["dst_vm_disk"] = json.dumps(
                vm_config_copy["dst_vm_disk"])
        if isinstance(vm_config_copy["dst_vm_os_disk"], dict):
            vm_config_copy["dst_vm_os_disk"] = json.dumps(
                vm_config_copy["dst_vm_os_disk"])
        if "dst_vm_data_disk" in vm_config_copy and \
                isinstance(vm_config_copy["dst_vm_data_disk"], dict):
            vm_config_copy["dst_vm_data_disk"] = json.dumps(
                vm_config_copy["dst_vm_data_disk"])
        if isinstance(vm_config_copy["dst_vm_net"], list):
            vm_config_copy["dst_vm_net"] = json.dumps(
                vm_config_copy["dst_vm_net"])
        if isinstance(vm_config_copy["dst_vm_image"], dict):
            vm_config_copy["dst_vm_image"] = json.dumps(
                vm_config_copy["dst_vm_image"])
        if isinstance(vm_config_copy["step"], dict):
            vm_config_copy["step"] = json.dumps(vm_config_copy["step"])
        return self.client_delegator.base_insert(table=self.table_vm,
                                                 columns=vm_config_copy)

    def list_vm(self, user_id=None, hyper_node_id=None, status=None,
                task_id=None, src_vm_id=None, is_delete=False, sort_key=None,
                reverse=True):
        condition = dict()
        if user_id:
            condition["user_id"] = user_id
        if hyper_node_id:
            condition["indeed_dst_node_id"] = hyper_node_id
        if status:
            condition["status"] = status
        if task_id:
            condition["task_id"] = task_id
        if src_vm_id:
            condition["src_vm_id"] = src_vm_id
        if is_delete:
            condition["is_delete"] = is_delete
        vms = self.client_delegator.base_get(
            table=self.table_vm,
            condition=condition,
            sort_key=sort_key,
            reverse=reverse,
            limit=self.max_query_count)

        for vm in vms:
            if isinstance(vm["src_vm_disk"], str):
                vm["src_vm_disk"] = json.loads(vm["src_vm_disk"])
            if isinstance(vm["src_vm_net"], str):
                vm["src_vm_net"] = json.loads(vm["src_vm_net"])
            if isinstance(vm["dst_vm_os_disk"], str):
                vm["dst_vm_os_disk"] = json.loads(vm["dst_vm_os_disk"])
            if "dst_vm_data_disk" in vm and isinstance(vm["dst_vm_data_disk"], str):
                vm["dst_vm_data_disk"] = json.loads(vm["dst_vm_data_disk"])
            if isinstance(vm["dst_vm_disk"], str):
                vm["dst_vm_disk"] = json.loads(vm["dst_vm_disk"])
            if isinstance(vm["dst_vm_net"], str):
                vm["dst_vm_net"] = json.loads(vm["dst_vm_net"])
            if isinstance(vm["dst_vm_image"], str):
                vm["dst_vm_image"] = json.loads(vm["dst_vm_image"])
            if isinstance(vm["step"], str):
                vm["step"] = json.loads(vm["step"])
        return vms

    def query_vm(self, session_id):
        condition = dict(session_id=session_id.strip(), is_delete=False)
        vms = self.client_delegator.base_get(
            table=self.table_vm,
            condition=condition,
            limit=self.max_query_count)
        if not vms:
            log_msg = "vm session not exists, session id: {session_id}" \
                      "".format(session_id=session_id)
            logger.error(log_msg)
            return None

        vm = dict(vms[0])
        if isinstance(vm["src_vm_disk"], str):
            vm["src_vm_disk"] = json.loads(vm["src_vm_disk"])
        if isinstance(vm["src_vm_net"], str):
            vm["src_vm_net"] = json.loads(vm["src_vm_net"])
        if isinstance(vm["dst_vm_os_disk"], str):
            vm["dst_vm_os_disk"] = json.loads(vm["dst_vm_os_disk"])
        if "dst_vm_data_disk" in vm and isinstance(vm["dst_vm_data_disk"], str):
            vm["dst_vm_data_disk"] = json.loads(vm["dst_vm_data_disk"])
        if isinstance(vm["dst_vm_disk"], str):
            vm["dst_vm_disk"] = json.loads(vm["dst_vm_disk"])
        if isinstance(vm["dst_vm_net"], str):
            vm["dst_vm_net"] = json.loads(vm["dst_vm_net"])
        if isinstance(vm["dst_vm_image"], str):
            vm["dst_vm_image"] = json.loads(vm["dst_vm_image"])
        if isinstance(vm["step"], str):
            vm["step"] = json.loads(vm["step"])
        return vm

    def update_vm(self, session_id, columns):
        columns_copy = deepcopy(columns)
        if columns_copy.has_key("extra"):
            del columns_copy["extra"]
        if columns_copy.has_key("src_vm_disk") and isinstance(
                columns_copy["src_vm_disk"], list):
            columns_copy["src_vm_disk"] = json.dumps(
                columns_copy["src_vm_disk"])
        if columns_copy.has_key("dst_vm_disk") and isinstance(
                columns_copy["dst_vm_disk"], list):
            columns_copy["dst_vm_disk"] = json.dumps(
                columns_copy["dst_vm_disk"])
        if columns_copy.has_key("src_vm_net") and isinstance(
                columns_copy["src_vm_net"], list):
            columns_copy["src_vm_net"] = json.dumps(columns_copy["src_vm_net"])
        if columns_copy.has_key("dst_vm_net") and isinstance(
                columns_copy["dst_vm_net"], list):
            columns_copy["dst_vm_net"] = json.dumps(columns_copy["dst_vm_net"])
        if columns_copy.has_key("dst_vm_os_disk") and isinstance(
                columns_copy["dst_vm_os_disk"], dict):
            columns_copy["dst_vm_os_disk"] = json.dumps(columns_copy["dst_vm_os_disk"])
        if columns_copy.has_key("dst_vm_data_disk") and isinstance(
                columns_copy["dst_vm_data_disk"], dict):
            columns_copy["dst_vm_data_disk"] = json.dumps(columns_copy["dst_vm_data_disk"])
        if columns_copy.has_key("dst_vm_image") and isinstance(
                columns_copy["dst_vm_image"], dict):
            columns_copy["dst_vm_image"] = json.dumps(columns_copy["dst_vm_image"])
        if columns_copy.has_key("step") and isinstance(columns_copy["step"], dict):
            columns_copy["step"] = json.dumps(columns_copy["step"])
        columns_copy["record_update_time"] = get_current_time()
        self.client_delegator.base_update(
            table=self.table_vm,
            condition=dict(session_id=session_id),
            columns=columns_copy)

    def delete_vm(self, session_id=None, user_id=None):
        condition = dict()
        if session_id:
            condition["session_id"] = session_id
        if user_id:
            condition["user_id"] = user_id
        self.client_delegator.base_delete(
            table=self.table_vm,
            condition=condition)

    ###########################################################################

    ###########################################################################
    def create_migrate_task(self, columns):
        columns_copy = deepcopy(columns)
        self.client_delegator.base_insert(table=self.table_migrate_task,
                                          columns=columns_copy)

    def list_migrate_task(self, user_id=None, dst_node_id=None,
                          is_delete=False):
        condition = dict()
        if user_id:
            condition["user_id"] = user_id
        if is_delete:
            condition["is_delete"] = is_delete
        if dst_node_id:
            condition["dst_node_id"] = dst_node_id
        return self.client_delegator.base_get(table=self.table_migrate_task,
                                              condition=condition,
                                              limit=self.max_query_count)

    def query_migrate_task(self, task_id):
        condition = dict(task_id=task_id.strip(), is_delete=False)
        tasks = self.client_delegator.base_get(
            table=self.table_migrate_task,
            condition=condition,
            limit=self.max_query_count)
        if not tasks:
            log_msg = "migrate task not exists, task id: {task_id}" \
                      "".format(task_id=task_id)
            logger.error(log_msg)
            return None
        return tasks[0]

    def update_migrate_task(self, task_id, columns):
        columns_copy = deepcopy(columns)
        columns_copy["record_update_time"] = get_current_time()
        self.client_delegator.base_update(
            table=self.table_migrate_task,
            condition=dict(task_id=task_id),
            columns=columns_copy)

    def delete_migrate_task(self, task_id=None, user_id=None):
        condition = dict()
        if task_id:
            condition["task_id"] = task_id
        if user_id:
            condition["user_id"] = user_id
        self.client_delegator.base_delete(
            table=self.table_migrate_task,
            condition=condition)

    ###########################################################################

    ###########################################################################
    def create_src_platform(self, columns):
        columns_copy = deepcopy(columns)
        if isinstance(columns_copy["resource"], list):
            columns_copy["resource"] = json.dumps(columns_copy["resource"])
        self.client_delegator.base_insert(table=self.table_src_platform,
                                          columns=columns_copy)

    def list_src_platform(self, user_id=None, is_delete=False):
        condition = dict()
        if user_id:
            condition["user_id"] = user_id
        if is_delete:
            condition["is_delete"] = is_delete
        return self.client_delegator.base_get(
            table=self.table_src_platform,
            condition=condition,
            limit=self.max_query_count)

    def query_src_platform(self, platform_id):
        condition = dict(platform_id=platform_id.strip(), is_delete=False)
        platforms = self.client_delegator.base_get(
            table=self.table_src_platform,
            condition=condition,
            limit=self.max_query_count)
        if not platforms:
            log_msg = "src platform not exists, platform id: {platform_id}" \
                      "".format(platform_id=platform_id)
            logger.error(log_msg)
            return None
        platform = platforms[0]
        if isinstance(platform["resource"], str):
            platform["resource"] = json.loads(platform["resource"])
        return platform

    def update_src_platform(self, platform_id, columns):
        columns_copy = deepcopy(columns)
        columns_copy["record_update_time"] = get_current_time()
        self.client_delegator.base_update(
            table=self.table_src_platform,
            condition=dict(platform_id=platform_id),
            columns=columns_copy)

    def delete_src_platform(self, platform_id=None, user_id=None):
        condition = dict()
        if platform_id:
            condition["platform_id"] = platform_id
        if user_id:
            condition["user_id"] = user_id
        self.client_delegator.base_delete(
            table=self.table_src_platform,
            condition=condition)
    ###########################################################################


class ZonePGInterface(PGInterface):
    db_name = DB_ZONE
    table_image = TB_IMAGE
    table_job = TB_JOB
    table_hyper_node = TB_HYPER_NODE
    table_hypernode_plg = TB_HYPERNODE_PLG
    table_place_group_rule = TB_PLACE_GROUP_RULE

    def __init__(self, min_connect=0, max_connect=1000):
        super(ZonePGInterface, self).__init__(self.db_name,
                                              min_connect,
                                              max_connect)

    ###########################################################################
    def query_image(self, image_id):
        images = self.client_delegator.base_get(
            table=self.table_image,
            condition=dict(image_id=image_id.strip()))
        return images[0] if images else None

    def insert_image(self, columns):
        self.client_delegator.base_insert(
            table=self.table_image,
            columns=columns)

    def update_image(self, image_id, columns):
        self.client_delegator.base_update(
            table=self.table_image,
            condition=dict(image_id=image_id),
            columns=columns)

    def delete_image(self, image_id):
        self.client_delegator.base_delete(
            table=self.table_image,
            condition=dict(image_id=image_id))

    ###########################################################################

    ###########################################################################
    def query_node(self, hyper_node_id):
        nodes = self.client_delegator.base_get(
            table=self.table_hyper_node,
            condition=dict(hyper_node_id=hyper_node_id.strip()))
        return nodes[0] if nodes else None

    def update_node(self, hyper_node_id, columns):
        self.client_delegator.base_update(
            table=self.table_image,
            condition=dict(hyper_node_id=hyper_node_id),
            columns=columns)

    ###########################################################################

    ###########################################################################
    def query_job(self, job_id, status=None):
        if status:
            condition = dict(job_id=job_id, status=status)
        else:
            condition = dict(job_id=job_id.strip())

        job_detail_list = self.client_delegator.base_get(
            table=self.table_job,
            condition=condition)

        return job_detail_list[0] if job_detail_list else None

    ###########################################################################

    ###########################################################################
    def list_node_plg(self, hyper_node_id=None, place_group_id=None):
        condition = dict()
        if hyper_node_id:
            condition["hyper_node_id"] = hyper_node_id
        if place_group_id:
            condition["place_group_id"] = place_group_id

        result = self.client_delegator.base_get(
            table=self.table_hypernode_plg,
            condition=condition)
        return result

    ###########################################################################

    ###########################################################################
    def list_place_group_rule(self, place_group_id):
        condition = dict()
        if place_group_id:
            condition["place_group_id"] = place_group_id

        result = self.client_delegator.base_get(
            table=self.table_place_group_rule,
            condition=condition)
        return result
    ###########################################################################
