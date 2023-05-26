# -*- coding: utf-8 -*-

from db.constants import (
    TB_V2V_MIGRATE_TASK,
    TB_V2V_VM,
    TB_V2V_SRC_PLATFORM
)
from fg import context
from fg.uutils.utils_common import now_local
from log.logger import logger
from utils.json import json_dump, json_load

ctx = context.instance()


class TableSrcPlatform(object):
    table = TB_V2V_SRC_PLATFORM

    def create_src_platform(self, platform_id, user_id, platform_type,
                            platform_ip, platform_port, platform_user,
                            platform_password, platform_name, platform_version,
                            status, resource):
        """创建源平台"""
        if isinstance(resource, list):
            resource = json_dump(resource)

        columns = dict()
        columns["platform_id"] = platform_id
        columns["user_id"] = user_id
        columns["platform_name"] = platform_name
        columns["platform_type"] = platform_type
        columns["platform_ip"] = platform_ip
        columns["platform_port"] = platform_port
        columns["platform_user"] = platform_user
        columns["platform_password"] = platform_password
        columns["platform_version"] = platform_version
        columns["status"] = status
        columns["resource"] = resource
        columns["record_create_time"] = now_local()
        columns["record_update_time"] = now_local()
        columns["is_delete"] = False

        logger.info(
            "add src platform start, platform id: {platform_id}, platform "
            "info: {platform_info}"
                .format(platform_id=platform_id, platform_info=columns))

        try:
            ctx.v2v_pg.base_insert(table=self.table, columns=columns)
        except Exception as e:
            err_msg = "add src platform failed, platform id: {platform_id}, " \
                      "err reason: {err_reason}" \
                      "".format(platform_id=platform_id,
                                err_reason=str(e))
            logger.error(err_msg)
            raise Exception(err_msg)

    def update_src_platform(self, platform_id, platform_ip, platform_port,
                            platform_user, platform_password, platform_name,
                            status, resource, platform_version):
        """更新源平台"""

        if isinstance(resource, list):
            resource = json_dump(resource)

        columns = dict()
        columns["platform_name"] = platform_name
        columns["platform_ip"] = platform_ip
        columns["platform_port"] = platform_port
        columns["platform_user"] = platform_user
        columns["platform_password"] = platform_password
        columns["platform_version"] = platform_version
        columns["status"] = status
        columns["resource"] = resource
        columns["record_create_time"] = now_local()
        columns["record_update_time"] = now_local()

        logger.info(
            "update src platform start, platform id: {platform_id}, platform "
            "info: {platform_info}"
                .format(platform_id=platform_id, platform_info=columns))
        try:
            res = ctx.v2v_pg.base_update(table=self.table,
                                         condition=dict(
                                             platform_id=platform_id),
                                         columns=columns)
            return res
        except Exception as e:
            err_msg = "update src platform failed, platform id: {platform_id}, err " \
                      "reason: {err_reason}".format(platform_id=platform_id,
                                                    err_reason=str(e))
            logger.error(err_msg)
            raise Exception(err_msg)

    def query_src_platform(self, platform_id):
        """获取某一个源平台信息"""
        try:
            platforms = ctx.v2v_pg.base_get(
                table=self.table,
                condition=dict(platform_id=platform_id,
                               is_delete=False))
            return platforms[0] if platforms else None
        except Exception as e:
            err_msg = "query src platform failed, platform id: {platform_id}, " \
                      "err reason: {err_reason}" \
                .format(platform_id=platform_id,
                        err_reason=str(e))
            logger.error(err_msg)
            raise Exception(err_msg)

    def list_src_platform(self, user_id, platform_id=None, platform_ip=None,
                          platform_user=None, is_delete=False):
        """展示所有的源平台信息"""
        logger.info("list src platform start, user id: {user_id}"
                    "".format(user_id=user_id))
        condition = dict(is_delete=is_delete)
        if user_id:
            condition["user_id"] = user_id
        if platform_id:
            condition["platform_id"] = platform_id
        if platform_ip:
            condition["platform_ip"] = platform_ip
        if platform_user:
            condition["platform_user"] = platform_user

        try:
            platforms = ctx.v2v_pg.base_get(
                table=self.table,
                condition=condition)
        except Exception as e:
            err_msg = "list src platform failed, user id: {user_id}, err " \
                      "reason: {err_reason}" \
                      "".format(user_id=user_id, err_reason=str(e))
            logger.error(err_msg)
            raise Exception(err_msg)

        for platform_info in platforms:
            if "resource" in platform_info:
                if isinstance(platform_info["resource"], str):
                    platform_info["resource"] = json_load(
                        platform_info["resource"])
        return platforms

    def delete_src_platform(self, platform_id):
        """删除源平台"""
        logger.info("delete src platform start, platform id: {platform_id}"
                    .format(platform_id=platform_id))
        try:
            res = ctx.v2v_pg.base_update(table=self.table,
                                         condition=dict(platform_id=platform_id),
                                         columns=dict(is_delete=True))
            return res
        except Exception as e:
            err_msg = "delete src platform failed, platform id: {platform_id}" \
                      ", err reason: {err_reason}" \
                      "".format(platform_id=platform_id, err_reason=str(e))
            logger.error(err_msg)
            raise Exception(err_msg)


class TableMigrateTask(object):
    table = TB_V2V_MIGRATE_TASK

    def create_migration_task(self, columns):
        columns["is_delete"] = False
        return ctx.v2v_pg.base_insert(table=self.table, columns=columns)

    def update_migration_task(self, condition, columns):
        return ctx.v2v_pg.base_update(table=self.table,
                                      condition=condition,
                                      columns=columns)

    def get_count(self, user_id=None, search_word=None, is_delete=False):
        condition = {"is_delete": is_delete}
        if user_id:
            condition["user_id"] = user_id
        if search_word:
            condition["search_word"] = search_word
        return ctx.v2v_pg.get_count(table=self.table, condition=condition)

    def query_migration_task(self, task_id, is_delete=False):
        condition = {"is_delete": is_delete, "task_id": task_id}
        tasks = ctx.v2v_pg.base_get(self.table, condition)
        return tasks[0] if tasks else None

    def list_migration_task(self, user_id=None, task_id=None,
                            src_platform_id=None, limit=None,
                            offset=None, search_word=None,
                            sort_key=None, reverse=False,
                            is_delete=False):
        condition = dict(is_delete=is_delete)
        if task_id:
            condition["task_id"] = task_id
        if user_id:
            condition["user_id"] = user_id
        if src_platform_id:
            condition["src_platform_id"] = src_platform_id
        if search_word:
            condition["search_word"] = search_word
        tasks = ctx.v2v_pg.base_get(table=self.table,
                                    condition=condition,
                                    limit=limit,
                                    offset=offset,
                                    sort_key=sort_key,
                                    reverse=reverse)
        return tasks


class TableVm(object):
    table = TB_V2V_VM

    def query_vm(self, session_id, columns=None):
        condition = {
            "is_delete": False,
            "session_id": session_id
        }
        db_result = ctx.v2v_pg.base_get(table=self.table,
                                        condition=condition,
                                        columns=columns)
        vm_info = db_result[0] if db_result else None
        if isinstance(vm_info["src_vm_disk"], str):
            vm_info["src_vm_disk"] = json_load(vm_info["src_vm_disk"])
        if isinstance(vm_info["src_vm_net"], str):
            vm_info["src_vm_net"] = json_load(vm_info["src_vm_net"])
        if isinstance(vm_info["dst_vm_os_disk"], str):
            vm_info["dst_vm_os_disk"] = json_load(vm_info["dst_vm_os_disk"])
        if isinstance(vm_info.get("dst_vm_data_disk"), str):
            vm_info["dst_vm_data_disk"] = json_load(vm_info["dst_vm_data_disk"])
        if isinstance(vm_info["dst_vm_disk"], str):
            vm_info["dst_vm_disk"] = json_load(vm_info["dst_vm_disk"])
        if isinstance(vm_info["dst_vm_net"], str):
            vm_info["dst_vm_net"] = json_load(vm_info["dst_vm_net"])
        if isinstance(vm_info["dst_vm_image"], str):
            vm_info["dst_vm_image"] = json_load(vm_info["dst_vm_image"])
        if isinstance(vm_info["step"], str):
            vm_info["step"] = json_load(vm_info["step"])
        return vm_info

    def list_vm(self, user_id=None, session_id=None, status=None,
                task_id=None, limit=None, offset=None,
                distinct=False, sort_key=None, reverse=True,
                is_delete=False):
        condition = dict(is_delete=is_delete)
        if user_id:
            condition["user_id"] = user_id
        if session_id:
            condition["session_id"] = session_id
        if status:
            condition["status"] = status
        if task_id:
            condition["task_id"] = task_id
        vm_list = ctx.v2v_pg.base_get(table=self.table,
                                      condition=condition,
                                      offset=offset,
                                      limit=limit,
                                      distinct=distinct,
                                      sort_key=sort_key,
                                      reverse=reverse)
        if not vm_list:
            logger.error("vm list is None, condition: %s" % condition)
            return vm_list

        for vm_info in vm_list:
            if isinstance(vm_info["src_vm_disk"], str):
                vm_info["src_vm_disk"] = json_load(vm_info["src_vm_disk"])
            if isinstance(vm_info["src_vm_net"], str):
                vm_info["src_vm_net"] = json_load(vm_info["src_vm_net"])
            if isinstance(vm_info["dst_vm_os_disk"], str):
                vm_info["dst_vm_os_disk"] = json_load(vm_info["dst_vm_os_disk"])
            if isinstance(vm_info.get("dst_vm_data_disk"), str):
                vm_info["dst_vm_data_disk"] = json_load(vm_info["dst_vm_data_disk"])
            if isinstance(vm_info["dst_vm_disk"], str):
                vm_info["dst_vm_disk"] = json_load(vm_info["dst_vm_disk"])
            if isinstance(vm_info["dst_vm_net"], str):
                vm_info["dst_vm_net"] = json_load(vm_info["dst_vm_net"])
            if isinstance(vm_info["dst_vm_image"], str):
                vm_info["dst_vm_image"] = json_load(vm_info["dst_vm_image"])
            if isinstance(vm_info["step"], str):
                vm_info["step"] = json_load(vm_info["step"])
        return vm_list

    def get_count(self, task_id=None, status=None, is_delete=False):
        condition = {"is_delete": is_delete}
        if task_id:
            condition["task_id"] = task_id
        if status:
            condition["status"] = status
        return ctx.v2v_pg.get_count(table=self.table, condition=condition)

    def update_vm(self, condition, columns):
        columns_keys = columns.keys()
        if "step" in columns_keys:
            columns["step"] = json_dump(columns["step"])
        if "src_vm_net" in columns_keys:
            columns["src_vm_net"] = json_dump(columns["src_vm_net"])
        if "src_vm_disk" in columns_keys:
            columns["src_vm_disk"] = json_dump(columns["src_vm_disk"])
        if "dst_vm_net" in columns_keys:
            columns["dst_vm_net"] = json_dump(columns["dst_vm_net"])
        if "dst_vm_disk" in columns_keys:
            columns["dst_vm_disk"] = json_dump(columns["dst_vm_disk"])
        if "dst_vm_os_disk" in columns_keys:
            columns["dst_vm_os_disk"] = json_dump(columns["dst_vm_os_disk"])
        if "dst_vm_data_disk" in columns_keys:
            columns["dst_vm_data_disk"] = json_dump(
                columns["dst_vm_data_disk"])
        if "dst_vm_image" in columns_keys:
            columns["dst_vm_image"] = json_dump(columns["dst_vm_image"])

        affcnt = ctx.v2v_pg.base_update(table=self.table,
                                        condition=condition,
                                        columns=columns)
        return affcnt

    def create_vm(self, columns):
        if isinstance(columns["src_vm_net"], list):
            columns["src_vm_net"] = json_dump(columns["src_vm_net"])
        if isinstance(columns["src_vm_disk"], list):
            columns["src_vm_disk"] = json_dump(columns["src_vm_disk"])
        if isinstance(columns["dst_vm_disk"], list):
            columns["dst_vm_disk"] = json_dump(columns["dst_vm_disk"])
        if isinstance(columns["dst_vm_os_disk"], dict):
            columns["dst_vm_os_disk"] = json_dump(columns["dst_vm_os_disk"])
        if "dst_vm_data_disk" in columns and isinstance(
                columns.get("dst_vm_data_disk"), dict):
            columns["dst_vm_data_disk"] = json_dump(
                columns["dst_vm_data_disk"])
        if isinstance(columns["dst_vm_net"], list):
            columns["dst_vm_net"] = json_dump(columns["dst_vm_net"])
        if isinstance(columns["dst_vm_image"], dict):
            columns["dst_vm_image"] = json_dump(columns["dst_vm_image"])
        if "step" in columns and isinstance(columns["step"], dict):
            columns["step"] = json_dump(columns["step"])

        columns["is_delete"] = False
        ctx.v2v_pg.base_insert(table=self.table, columns=columns)
