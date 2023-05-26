# -*- coding: utf-8 -*-

from fg.dto import BaseDto


class TaskDto(BaseDto):

    def __init__(self,
                 task_id=None,
                 console_id=None,
                 owner_id=None,
                 task_name=None,
                 task_desc=None,
                 user_id=None,
                 task_pattern=None,
                 region=None,
                 zone=None,
                 src_datacenter_name=None,
                 hyper_node=None,
                 src_platform_id=None):
        self.task = None
        self.task_id = task_id
        self.console_id = console_id
        self.owner_id = owner_id
        self.task_name = task_name
        self.task_desc = task_desc
        self.user_id = user_id
        self.task_pattern = task_pattern
        self.region = region
        self.zone = zone
        self.src_datacenter_name = src_datacenter_name
        self.src_platform_id = src_platform_id
        self.hyper_node = hyper_node
        self._info = None

    @property
    def info(self):
        if self._info is None:
            task_data = {
                "task_id": self.task_id,
                "console_id": self.console_id,
                "owner_id": self.owner_id,
                "task_name": self.task_name,
                "task_desc": self.task_desc,
                "user_id": self.user_id,
                "task_pattern": self.task_pattern,
                "region": self.region,
                "zone": self.zone
            }
            if self.src_platform_id:
                task_data["src_platform_id"] = self.src_platform_id
            if self.src_datacenter_name:
                task_data["src_datacenter_name"] = self.src_datacenter_name
            if self.hyper_node:
                task_data["dst_node_id"] = self.hyper_node
            else:
                task_data["dst_node_id"] = "auto"

        return self._info