# -*- coding: utf-8 -*-

from log.logger import logger

from uutils.common import normal_exec


def copy_nfs_file(nfs_file_path, local_file_path, timeout=60):
    """从nfs拷贝文件到本地"""
    from constants.common import UPLOAD_IMAGE_LD_NFS_SO_PATH
    cmd = "LD_PRELOAD={ld_nfs_so} cp {nfs_file_path} {local_file_path}".format(
        ld_nfs_so=UPLOAD_IMAGE_LD_NFS_SO_PATH,
        nfs_file_path=nfs_file_path,
        local_file_path=local_file_path)
    logger.info("copy nfs file to local ready, copy cmd: {cmd}".format(cmd=cmd))
    returncode, _, stderr = normal_exec(cmd, timeout)
    if returncode != 0:
        log_msg = "copy nas file to local failed, copy cmd: {cmd}, error " \
                  "reason: {error_reason}" \
                  "".format(cmd=cmd, error_reason=stderr)

        logger.exception(log_msg)
        raise Exception(log_msg)
