# -*- coding: utf-8 -*-

"""功能：定义虚拟机的类"""

import os
import shutil

from contextlib import contextmanager

from log.logger import logger
from utils.misc import get_current_time

from base import Base
from task import MigrateTask
from context import WorkerContext
from hyper_node import HyperNode

from constants.common import (
    MigratePattern,
    MigrateStatus,
    CLEAN_AFTER_FAILED
)
from constants.iaas import ImageStatus

from migration import (
    ExportImageMigration,
    UploadImageMigration
)
from checker import (
    ExportImageChecker,
    UploadImageChecker
)


CTX = WorkerContext()


class VMSessionBase(Base):
    """通用虚拟机类"""
    def __init__(self, session_id):
        super(VMSessionBase, self).__init__()
        self._session_id = session_id
        self._info = None

    @property
    def session_id(self):
        return self._session_id


class VMSession(VMSessionBase):
    """虚拟机会话类"""

    def __init__(self, session_id):
        super(VMSession, self).__init__(session_id)
        self._info = dict()

    @property
    def info(self):
        if not self._info:
            self._info = CTX.v2v_pg.query_vm(self.session_id)
        return self._info

    @info.setter
    def info(self, value):
        if not self._info:
            self._info = value
        else:
            self._info.update(value)

    def migration(self):
        """迁移器"""
        if self.task.task_pattern == MigratePattern.EXPORT_IMAGE.value:
            return ExportImageMigration(self)
        if self.task.task_pattern == MigratePattern.UPLOAD_IMAGE.value:
            return UploadImageMigration(self)

    def checker(self):
        """检查器"""
        if self.task.task_pattern == MigratePattern.EXPORT_IMAGE.value:
            return ExportImageChecker(self)
        if self.task.task_pattern == MigratePattern.UPLOAD_IMAGE.value:
            return UploadImageChecker(self)

    @property
    def src_vm_id(self):
        return self.info["src_vm_id"]

    @property
    def dst_vm_id(self):
        return self.info["dst_vm_id"]

    @dst_vm_id.setter
    def dst_vm_id(self, dst_vm_id):
        self.info.update(dict(dst_vm_id=dst_vm_id))

    @property
    def dst_vm_image(self):
        return self.info["dst_vm_image"]

    @property
    def dst_vm_image_id(self):
        return self.dst_vm_image["image_id"]

    @property
    def src_vm_status(self):
        """获取源虚拟机的实时状态"""
        return self.task.src_platform.get_vm_status(self.src_vm_id)

    @property
    def src_vm_name(self):
        return self.info["src_vm_name"]

    @property
    def src_vm_os_type(self):
        return self.info["src_vm_os_type"]

    @property
    def src_vm_folder(self):
        """eg: wuhan/resource """
        return self.info["src_vm_folder"]

    @property
    def src_vm_nfs_path(self):
        """eg: nfs://192.168.12.98/mnt/worker/centos_6.3_simple """
        return self.info["src_vm_nfs_path"]

    @property
    def err_msg(self):
        return self.info["err_msg"]

    @property
    def err_code(self):
        return self.info["err_code"]

    @property
    def step(self):
        return self.info["step"]

    @property
    def process(self):
        return self.info["process"]

    @property
    def status(self):
        return self.info["status"]

    @status.setter
    def status(self, status):
        self.info.update(dict(status=status))

    @property
    def task_id(self):
        return self.info["task_id"]

    @property
    def task(self):
        return MigrateTask(self.task_id)

    @property
    def dst_vm_name(self):
        return self.info["dst_vm_name"]

    @property
    def dst_vm_type(self):
        return self.info["dst_vm_type"]

    @property
    def dst_vm_os_type(self):
        return self.info["dst_vm_os_type"]

    @property
    def indeed_dst_node_id(self):
        return self.info["indeed_dst_node_id"]

    @property
    def indeed_dst_node(self):
        return HyperNode(self.indeed_dst_node_id)

    @property
    def dst_vm_net(self):
        return self.info["dst_vm_net"]

    @property
    def dst_vm_cpu(self):
        return self.info["dst_vm_cpu_core"]

    @property
    def dst_vm_memory(self):
        return self.info["dst_vm_memory"]

    @property
    def dst_vm_disk(self):
        return self.info.get("dst_vm_disk")

    @property
    def dst_vm_data_disk(self):
        """获取目标虚拟机的数据盘信息
        若没有数据盘，则返回空列表
        返回值为列表，列表中的每一个元素为磁盘的详情字典
        """
        dst_vm_data_disk = list()
        for disk_info in self.dst_vm_disk:
            if disk_info["is_os_disk"] is False:
                dst_vm_data_disk.append(disk_info)
        return dst_vm_data_disk

    @property
    def dst_vm_os_disk(self):
        """获取目标虚拟机的系统盘信息
        返回值为磁盘的详情字典
        """
        for disk_info in self.dst_vm_disk:
            if disk_info.get("is_os_disk", None):
                return disk_info

    @property
    def dst_vm_disk_num(self):
        return len(self.dst_vm_disk)

    @property
    def dst_vm_has_data_disk(self):
        return bool(self.dst_vm_data_disk)

    @property
    def export_dir(self):
        """导出的基准目录
        非数据库保存字段，调用时请留意"""
        if "extra" in self.info and "export_dir" in self.info["extra"]:
            return self.info["extra"]["export_dir"]
        return ""

    @property
    def upload_dir(self):
        """上传的基准目录
        非数据库保存字段，调用时请留意"""
        if "extra" in self.info and "upload_dir" in self.info["extra"]:
            return self.info["extra"]["upload_dir"]
        return ""

    def migrate(self):
        """源主机迁移"""
        with self._migrate() as pre_check:
            if pre_check:
                try:
                    self.migration().migrate()
                except Exception:
                    logger.error("vm migrate failed, session id: {session_id}"
                                 "".format(session_id=self.session_id))

            if self.status != MigrateStatus.FAILED.value:
                return self.clean()

            # 失败后清理垃圾
            if CTX.zone_pg.query_image(self.dst_vm_image_id):
                columns = dict(status=ImageStatus.CEASED.value)
                logger.info("vm has migrate failed, try to ceased "
                            "image, session id: {session_id}"
                            "".format(session_id=self.session_id))
                CTX.zone_pg.update_image(self.dst_vm_image_id, columns=columns)

            # 只有当任务的状态为失败，开启了失败以后删除的按钮，才用执行删除垃圾
            if CLEAN_AFTER_FAILED:
                return self.clean()

    @contextmanager
    def _migrate(self):
        """执行迁移"""

        # 前置检查
        pre_check = self.checker().check()
        yield pre_check

        # 清理
        if not pre_check:
            self.clean()

    def update_to_mem(self, data):
        """更新虚拟机任务信息到内存"""
        self.info.update(data)

    def update_to_pg(self, data=None):
        """更新虚拟机任务信息到数据库"""
        CTX.v2v_pg.update_vm(session_id=self.session_id, columns=data)

    def update_to_mem_and_pg(self, data):
        """更新虚拟机任务信息到内存和数据库"""
        # 更新虚拟机任务信息到内存
        self.update_to_mem(data)

        # 更新虚拟机任务信息到数据库
        self.update_to_pg(data)

    def update_detail_migrate_status(self, detail_status):
        """更新详细的迁移状态到内存和数据库"""
        status = ""
        if "status" in detail_status:
            status = detail_status["status"]
        if status in MigrateStatus.list_end_migrate_status():
            detail_status["end_time"] = get_current_time()
        self.update_to_mem_and_pg(detail_status)
        
    def clean(self):
        """清理"""

        # 清理导出目录
        if os.path.isdir(self.export_dir):
            shutil.rmtree(self.export_dir)
            logger.info("delete export directory end, session id: "
                        "{session_id}, export dir: {export_dir}"
                        .format(session_id=self.session_id,
                                export_dir=self.export_dir))

        # 清理上传目录
        if os.path.isdir(self.upload_dir):
            shutil.rmtree(self.upload_dir)
            logger.info("delete upload directory end, session id: "
                        "{session_id}, upload dir: {upload_dir}"
                        .format(session_id=self.session_id,
                                upload_dir=self.upload_dir))
