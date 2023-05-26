# -*- coding: utf-8 -*-

"""功能：通用常量定义"""

import os
import socket

from enum import Enum

from utils.net import get_hostname
from utils.yaml_tool import yaml_load

# 当前节点信息
LOCAL_NODE_ID = get_hostname().strip()
LOCAL_NODE_IP = socket.gethostbyname(LOCAL_NODE_ID)

# worker worker配置
V2V_WORKER_CONF_FILE_PATH = "/pitrix/conf/v2v_worker.yaml"
with open(V2V_WORKER_CONF_FILE_PATH, "r") as f:
    V2V_WORKER_YAML_CONFIG = yaml_load(f)

# V2V worker自身属性
DATA_DIR = V2V_WORKER_YAML_CONFIG["self"]["data_dir"]
DEPLOY_DIR = V2V_WORKER_YAML_CONFIG["self"]["deploy_dir"]
DEPLOY_MISC_DIR = os.path.join(DEPLOY_DIR, "worker/misc")

# 功能设置
CONCURRENCY_MIGRATE = V2V_WORKER_YAML_CONFIG["setting"]["concurrency_migrate"]
MAX_MIGRATING_NUM = V2V_WORKER_YAML_CONFIG["setting"]["max_migrating_num"]
CLEAN_AFTER_FAILED = V2V_WORKER_YAML_CONFIG["setting"]["clean_after_failed"]
VM_MAX_MIGRATE_TIMEOUT = V2V_WORKER_YAML_CONFIG["setting"]["vm_max_migrate_timeout"]

# 迁移全局
INDEED_START_MIGRATE_TIMEOUT = 60 * 5
INDEED_END_MIGRATE_TIMEOUT = VM_MAX_MIGRATE_TIMEOUT

# 导出镜像
EXPORT_IMAGE_LOG_PATH = "/pitrix/log/ovftool.log"  # # VMware OVF Tool工具日志路径
EXPORT_IMAGE_LOG_LEVEL = "warning"  # # VMware OVF Tool工具日志级别
EXPORT_IMAGE_LOG_TO_CONSOLE = ""  # # VMware OVF Tool工具日志是否控制台显示
EXPORT_IMAGE_DST_BASE_DIR = os.path.join(DATA_DIR, "v2v_export")
EXPORT_IMAGE_DST_FORMAT_OVA = "ova"
EXPORT_IMAGE_TIMEOUT = 3600 * 24
EXPORT_IMAGE_MAX_RETRY_TIMES = 5
EXPORT_IMAGE_CMD_VI_PREFIX = "vi://"  # 全称"VMware Infrastructure"，作为OVF命令行选项，在服务器的凭据和路径之前使用
EXPORT_IMAGE_CMD_NOSSLVERIFY = "--noSSLVerify"  # 跳过连接时的SSL校验
EXPORT_IMAGE_CMD_OVERWRITE = "--overwrite"  # 导出的文件名已存在，强制重写
EXPORT_IMAGE_CMD_MACHINEOUTPUT = "--machineOutput"  # 以机器可读的格式输出ovftool的信息
EXPORT_IMAGE_CMD_QUIET = "--quiet"  # 仅仅打印输出错误消息
EXPORT_IMAGE_CMD_NOIMAGEFILES = "--noImageFiles"  # 不导出CD_ROM
EXPORT_IMAGE_CMD_POWEROFFSOURCE = "--powerOffSource"  # 确保虚拟机在被导出之前处于关机的状态
EXPORT_IMAGE_CMD_NONVRAMFILE = "--noNvramFile"  # 跨vsphere版本时，忽略nvram文件
EXPORT_IMAGE_CMD_ACCEPTALLEULAS = "--acceptAllEulas"  # 接受所有最终用户许可协议(EULAs)，而无需出现任何提示
EXPORT_IMAGE_CMD_LOG_LEVEL = "--X:logLevel=" + EXPORT_IMAGE_LOG_LEVEL
EXPORT_IMAGE_CMD_LOG_PATH = "--X:logFile=" + EXPORT_IMAGE_LOG_PATH
EXPORT_IMAGE_CMD_LOG_TO_CONSOLE = "--X:logToConsole" + EXPORT_IMAGE_LOG_TO_CONSOLE
EXPORT_IMAGE_DEFAULT_PARAMS = " ".join([EXPORT_IMAGE_CMD_NOSSLVERIFY,
                                        EXPORT_IMAGE_CMD_OVERWRITE,
                                        EXPORT_IMAGE_CMD_MACHINEOUTPUT,
                                        EXPORT_IMAGE_CMD_QUIET,
                                        EXPORT_IMAGE_CMD_NOIMAGEFILES,
                                        EXPORT_IMAGE_CMD_POWEROFFSOURCE,
                                        EXPORT_IMAGE_CMD_NONVRAMFILE,
                                        EXPORT_IMAGE_CMD_ACCEPTALLEULAS,
                                        EXPORT_IMAGE_CMD_LOG_LEVEL,
                                        EXPORT_IMAGE_CMD_LOG_PATH,
                                        EXPORT_IMAGE_CMD_LOG_TO_CONSOLE])


# 上传镜像
UPLOAD_IMAGE_LD_NFS_SO_PATH = V2V_WORKER_YAML_CONFIG["resource"]["lib"]["ld_nfs_so"]
UPLOAD_IMAGE_DST_BASE_DIR = os.path.join(DATA_DIR, "v2v_upload")
UPLOAD_IMAGE_TIMEOUT = 3600 * 24

# 处理镜像
DEAL_IMAGE_SRC_FORMAT_VMDK = "vmdk"
DEAL_IMAGE_DST_FORMAT_QCOW2 = "qcow2"
DEAL_IMAGE_CONVERT_IMAGE_TIMEOUT = 3600 * 24
DEAL_IMAGE_MOUNT_BASE_DIR = os.path.join(DATA_DIR, "v2v_mount")
DEAL_IMAGE_FILE_LOCK_BASE_DIR = os.path.join(DATA_DIR, "v2v_lock")


# 创建虚拟机
CREATE_INSTANCE_IMAGE_FILE_PATH = os.path.join(DEPLOY_MISC_DIR, "template.lz4")
CREATE_INSTANCE_RUN_INSTANCE_TIMEOUT = 60 * 30
CREATE_INSTANCE_START_INSTANCE_TIMEOUT = 60 * 20
CREATE_INSTANCE_RESTART_INSTANCE_TIMEOUT = 60 * 20
CREATE_INSTANCE_STOP_INSTANCE_TIMEOUT = 60 * 20
CREATE_INSTANCE_CREATE_VOLUMES_TIMEOUT = 60 * 20
CREATE_INSTANCE_ATTACH_VOLUMES_TIMEOUT = 60 * 10


# 覆盖镜像
COVER_IMAGE_TIMEOUT = 3600 * 24


class WorkerAction(Enum):
    """worker动作"""
    IMMEDIATELY_MIGRATE = "immediately_migrate"         # 立即执行
    TIME_MIGRATE = "time_migrate"                       # 定时执行


class MigratePattern(Enum):
    """迁移模式"""
    EXPORT_IMAGE = "export_image"                       # 导出镜像
    UPLOAD_IMAGE = "upload_image"                       # 上传镜像


class MigrateStep(Enum):
    """迁移步骤"""
    EXPORT_IMAGE = "export_image"                       # 导出镜像
    UPLOAD_IMAGE = "upload_image"                       # 上传镜像
    DEAL_IMAGE = "deal_image"                           # 处理镜像
    CREATE_INSTANCE = "create_instance"                 # 创建虚拟机
    COVER_IMAGE = "cover_image"                         # 覆盖镜像
    RECORRECT_AND_OPTIMIZE = "recorrect_and_optimize"   # 修复调优


class MigrateProcess(Enum):
    """迁移进度"""
    # 导出镜像
    START_EXPORT_IMAGE_PROCESS = 5                      # 开始导出镜像进度
    END_EXPORT_IMAGE_PROCESS = 25                       # 结束导出镜像进度

    # 上传镜像
    START_UPLOAD_IMAGE_PROCESS = 5                      # 开始上传镜像进度
    END_UPLOAD_IMAGE_PROCESS = 25                       # 结束上传镜像进度

    # 处理镜像
    START_DEAL_IMAGE_PROCESS = 30                       # 开始处理镜像进度
    END_DEAL_IMAGE_PROCESS = 50                         # 结束处理镜像进度

    # 创建虚拟机
    START_CREATE_INSTANCE_PROCESS = 55                  # 开始创建虚拟机进度
    END_CREATE_INSTANCE_PROCESS = 70                    # 结束创建虚拟机进度

    # 覆盖镜像
    START_COVER_IMAGE_PROCESS = 75                      # 开始覆盖镜像进度
    END_COVER_IMAGE_PROCESS = 90                        # 结束覆盖镜像进度

    # 修复调优
    START_RECORRECT_AND_OPTIMIZE_PROCESS = 95           # 开始修复调优进度
    END_RECORRECT_AND_OPTIMIZE_PROCESS = 100            # 结束修复调优进度


class MigrateStatus(Enum):
    """迁移状态"""
    READY = "ready"                                     # 就绪
    QUEUING = "queuing"                                 # 排队中
    PENDING = "pending"                                 # 重试排队中
    RUNNING = "running"                                 # 运行中
    COMPLETED = "completed"                             # 已完成
    FAILED = "failed"                                   # 失败

    @classmethod
    def list_wait_migrate_status(cls):
        """等待迁移的的状态列表"""
        return [cls.QUEUING.value, cls.PENDING.value]

    @classmethod
    def list_end_migrate_status(cls):
        """处于终态的状态列表"""
        return [cls.COMPLETED.value, cls.FAILED.value]


class RunningDetailMigrateStatus(Enum):
    """迁移中时详细的子步骤进度和状态"""

    # 开始导出镜像时的详细状态
    START_EXPORT_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.EXPORT_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.START_EXPORT_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 结束导出镜像时的详细状态
    END_EXPORT_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.EXPORT_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.END_EXPORT_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 开始上传镜像时的详细状态
    START_UPLOAD_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.UPLOAD_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.START_UPLOAD_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 结束上传镜像时的详细状态
    END_UPLOAD_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.UPLOAD_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.END_UPLOAD_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 开始处理镜像时的详细状态
    START_DEAL_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.DEAL_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.START_DEAL_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 结束处理镜像时的详细状态
    END_DEAL_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.DEAL_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.END_DEAL_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 开始创建虚拟机时的详细状态
    START_CREATE_INSTANCE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.CREATE_INSTANCE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.START_CREATE_INSTANCE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 结束创建虚拟机时的详细状态
    END_CREATE_INSTANCE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.CREATE_INSTANCE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.END_CREATE_INSTANCE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 开始覆盖镜像时的详细状态
    START_COVER_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.COVER_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.START_COVER_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 结束覆盖镜像时的详细状态
    END_COVER_IMAGE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.COVER_IMAGE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.END_COVER_IMAGE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 开始修复调优时的详细状态
    START_RECORRECT_AND_OPTIMIZE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.RECORRECT_AND_OPTIMIZE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.START_RECORRECT_AND_OPTIMIZE_PROCESS.value,
        status=MigrateStatus.RUNNING.value
    )

    # 结束修复调优时的详细状态
    END_RECORRECT_AND_OPTIMIZE_DETAIL_STATUS = dict(
        step=dict(
            step=MigrateStep.RECORRECT_AND_OPTIMIZE.value,
            err_msg="",
            err_code=0
        ),
        process=MigrateProcess.END_RECORRECT_AND_OPTIMIZE_PROCESS.value,
        status=MigrateStatus.COMPLETED.value
    )
