# -*- coding: utf-8 -*-

import os
import time

from log.logger import logger
from contextlib import contextmanager
from uutils.common import normal_exec
from utils.pitrix_folder import PitrixFolder
from utils.misc import FileLock

from constants.template import (
    QBD_MAP_CMD_TEMPLATE,
    QBD_DEV_PATH_TEMPLATE,
    QBD_UNMAP_CMD_TEMPLATE
)


@contextmanager
def map_qbd_device_context(volume_id):
    """连接到qbd设备，本质上是将NeonSAN磁盘映射为qbd网络块设备"""

    # 设备建立连接
    try:
        with FileLock(PitrixFolder.get_nbd_lock()):
            dev_path = map_qbd_device(volume_id)
    except Exception:
        yield None
    else:
        yield dev_path

    ###########################################################################
    # 下文
    with FileLock(PitrixFolder.get_nbd_lock()):
        unmap_qbd_device(volume_id)


def map_qbd_device(volume_id, pool="vol"):
    """设备建立连接，本质上是将NeonSAN磁盘映射为qbd网络块设备"""

    try:
        with FileLock(PitrixFolder.get_nbd_lock()):
            normal_exec(QBD_MAP_CMD_TEMPLATE.format(volume_id=volume_id, pool=pool))
    except Exception as e:
        log_msg = "connect to qbd device failed, volume id: %s, error reason: " \
                  "%s" % (volume_id, e)
        logger.error(log_msg)
        raise Exception(log_msg)

    dev_path = QBD_DEV_PATH_TEMPLATE.format(volume_id=volume_id, pool=pool)
    return dev_path


def unmap_qbd_device(volume_id, pool="vol"):
    """qbd设备解除映射"""

    # 断开设备连接
    QBD_UNMAP_CMD_TEMPLATE.format(volume_id=volume_id, pool=pool)

    # 清理设备残余进程
    # clean_cmd = "ps -C qbd -o pid=,command= | grep '%s' | awk '{print $1}'" % dev_path
    # returncode, stdout, stderr = normal_exec(clean_cmd)
    # if returncode == 0:
    #     pids = stdout.splitlines()
    #     for pid in pids:
    #         normal_exec("kill -9 %s" % pid)


@contextmanager
def mount_qbd_device_context(mnt_dir, dev_path, option="ro"):
    """挂载设备
    成功则返回True，失败抛出异常
    """
    # 挂载设备
    try:
        with FileLock(PitrixFolder.get_nbd_lock()):
            mount_qbd_device(mnt_dir, dev_path, option)
    except Exception:
        yield False
    else:
        yield True

    # 卸载设备
    with FileLock(PitrixFolder.get_nbd_lock()):
        umount_qbd_device(mnt_dir, dev_path)


def mount_qbd_device(mnt_dir, dev_path, option="ro"):
    """挂载
    成功返回True,失败抛出异常
    """

    mount_cmd = "mount {dev_path} {mnt_dir} -o {option}".format(
        dev_path=dev_path, mnt_dir=mnt_dir, option=option)
    logger.info("mount qbd device is ready, mnt dir: %s, dev path: %s, mount "
                "cmd: %s"
                % (mnt_dir, dev_path, mount_cmd))
    for i in range(3):
        # 挂载
        os.makedirs(mnt_dir) if not os.path.isdir(mnt_dir) else None
        normal_exec(mount_cmd, timeout=120)

        # 检验是否成功
        if option == "ro":
            returncode, stdout, stderr = normal_exec(
                "mount | grep %s | grep '(ro'" % mnt_dir)
        else:
            returncode, stdout, stderr = normal_exec(
                "mount | grep %s | grep '(rw'" % mnt_dir)
        if returncode == 0 and stdout != "":
            logger.info("mount qbd device successfully, mnt dir: %s, dev path:"
                        " %s, mount cmd: %s"
                        % (mnt_dir, dev_path, mount_cmd))
            return True
        time.sleep(3)
    else:
        log_msg = "mount nbd device failed, mnt dir: %s, dev path: %s, " \
                  "mount cmd: %s" \
                  % (mnt_dir, dev_path, mount_cmd)
        logger.error(log_msg)
        raise Exception(log_msg)


def umount_qbd_device(mnt_dir, dev_path):
    logger.info("umount device is ready, mnt dir: %s, dev path: %s"
                % (mnt_dir, dev_path))
    for i in range(10):
        # 刷新缓冲
        normal_exec("blockdev --flushbufs %s" % dev_path)

        # 卸载挂载目录
        normal_exec("umount %s" % mnt_dir, timeout=60)
        if not os.path.isdir(mnt_dir):
            logger.info("umount device successfully, mnt dir: %s, dev path: %s"
                        % (mnt_dir, dev_path))
            return

        normal_exec("rm -rf %s" % mnt_dir)
        if os.path.isdir(mnt_dir):
            logger.critical("mnt dir can't be removed, please check, "
                            "mnt dir: {mnt_dir}".format(mnt_dir=mnt_dir))
            time.sleep(3)
            continue
        return
    else:
        log_msg = "mount device failed, mnt dir: %s, dev path: %s" \
                  "" % (mnt_dir, dev_path)
        logger.error(log_msg)
        # raise Exception(log_msg)
