# -*- coding: utf-8 -*-

import time
import os

from log.logger import logger

from utils.image_tool import (
    get_nbd_device,
    open_nbd,
    clean_mnt,
    close_nbd
)
from contextlib import contextmanager
from uutils.common import normal_exec
from utils.pitrix_folder import PitrixFolder
from utils.misc import FileLock


@contextmanager
def map_nbd_device_context(img_path):
    """连接到nbd设备，本质上是将镜像文件映射为nbd网络块设备"""

    # 设备建立连接
    dev_path = map_nbd_device(img_path)
    img_info = dict(dev_path=dev_path, img_path=img_path,
                    has_partition=True, partition_info=dict())

    # 判断是否有分区
    cmd = "blkid | grep %sp" % dev_path
    returncode, stdout, stderr = normal_exec(cmd)
    if returncode != 0 or stdout == "":
        img_info["has_partition"] = False

    # 获取分区列表
    fdisk_cmd = "fdisk -l %s | grep %s | awk -F ' ' '{if(NR>1)print $1}'" % (dev_path, dev_path)
    returncode, stdout, stderr = normal_exec(fdisk_cmd)
    indeed_dev_path_list = []
    if returncode == 0 and stdout:
        indeed_dev_path_list = stdout.split("\n")

    # 指定分区和挂载点的映射关系
    dev_path_with_tag = dev_path + "p"
    partition_info = img_info["partition_info"]

    for indeed_dev_path in indeed_dev_path_list:
        assert dev_path_with_tag in indeed_dev_path
        partition = int(indeed_dev_path.split(dev_path_with_tag)[-1])
        base_mnt_dir = PitrixFolder.get_image_mnt(img_path)
        partition_mnt_dir = os.path.join(base_mnt_dir, str(partition))
        partition_info[indeed_dev_path] = partition_mnt_dir

    logger.info("map nbd device successfully, img path: {img_path}, img "
                "info: {img_info}"
                "".format(img_path=img_path, img_info=img_info))

    yield img_info

    ###########################################################################
    # 下文
    with FileLock(PitrixFolder.get_nbd_lock()):
        unmap_nbd_device(dev_path)


def map_nbd_device(img_path):
    """设备建立连接，本质上是将镜像文件映射为nbd网络块设备"""
    try:
        with FileLock(PitrixFolder.get_nbd_lock()):
            dev_path = get_nbd_device(img_path)
            open_nbd(dev_path, img_path, readonly=1)
    except Exception as e:
        log_msg = "connect to nbd device failed, image file: %s, error reason: " \
                  "%s" % (img_path, e)
        logger.error(log_msg)
        raise Exception(log_msg)

    if not dev_path:
        log_msg = "connect to nbd device failed, image file: %s, error reason: " \
                  "dev path is not connected" % img_path
        logger.error(log_msg)
        raise Exception(log_msg)
    return dev_path


def unmap_nbd_device(dev_path):
    """nbd设备解除映射"""

    # 刷新设备缓冲
    normal_exec("blockdev --flushbufs %s" % dev_path)

    # 断开设备连接
    close_nbd(dev_path)

    # 清理设备残余进程
    clean_cmd = "ps -C qemu-nbd,qemu-nbd-4.0 -o pid=,command= | grep '%s' | awk '{print $1}'" % dev_path
    returncode, stdout, stderr = normal_exec(clean_cmd)
    if returncode == 0:
        pids = stdout.splitlines()
        for pid in pids:
            normal_exec("kill -9 %s" % pid)


@contextmanager
def mount_nbd_device_context(mnt_dir, dev_path, option="ro"):
    """挂载设备
    成功则返回True，失败抛出异常
    """
    # 挂载设备
    try:
        mount_nbd_device(mnt_dir, dev_path, option)
    except Exception:
        yield False
    else:
        yield True

    # 卸载设备
    umount_nbd_device(mnt_dir, dev_path)


def mount_nbd_device(mnt_dir, dev_path, option="ro"):
    """挂载
    成功返回True,失败抛出异常
    """
    mount_cmd = "mount {dev_path} {mnt_dir} -o {option}".format(
        dev_path=dev_path, mnt_dir=mnt_dir, option=option)
    logger.info("mount nbd device is ready, mnt dir: %s, dev path: %s, mount "
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
            logger.info("mount nbd device successfully, mnt dir: %s, dev path:"
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


def umount_nbd_device(mnt_dir, dev_path):
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

        if clean_mnt(mnt_dir) == -1:
            time.sleep(3)
            continue
    else:
        log_msg = "mount device failed, mnt dir: %s, dev path: %s" \
                  "" % (mnt_dir, dev_path)
        logger.error(log_msg)
        # raise Exception(log_msg)
