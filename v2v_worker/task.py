# -*- coding: utf-8 -*-

"""功能：定义迁移任务类、迁移任务中的源主机类"""

from base import Base
from src_platform import VMWarePlatform
from context import WorkerContext
from constants.common import MigratePattern

CTX = WorkerContext()


# 迁移模式映射
MIGRATE_PATTERN_MAPPER = {
    1: MigratePattern.EXPORT_IMAGE.value,
    2: MigratePattern.UPLOAD_IMAGE.value
}


class MigrateTask(Base):
    """迁移任务类"""
    def __init__(self, task_id):
        super(MigrateTask, self).__init__()
        self._task_id = task_id
        self._config = dict()

    @property
    def task_id(self):
        return self._task_id

    @property
    def config(self):
        if not self._config:
            self._config = CTX.v2v_pg.query_migrate_task(self.task_id)
        return self._config

    @property
    def owner_id(self):
        return self.config["owner_id"]

    @property
    def task_name(self):
        return self.config["task_name"]

    @property
    def task_pattern(self):
        task_pattern_enum = self.config["task_pattern"]
        return MIGRATE_PATTERN_MAPPER[task_pattern_enum]

    @property
    def src_platform_id(self):
        return self.config["src_platform_id"]

    @property
    def src_platform(self):
        return VMWarePlatform(self.src_platform_id)

    @property
    def src_cluster_name(self):
        return self.config["src_cluster_name"]

    @property
    def src_datacenter_name(self):
        return self.config["src_datacenter_name"]

    @property
    def console_id(self):
        return self.config["console_id"]

    @property
    def dst_node_id(self):
        return self.config["dst_node_id"]

    @property
    def dst_zone_id(self):
        return self.config["dst_zone_id"]

    @property
    def dst_region_id(self):
        return self.config["dst_region_id"]
