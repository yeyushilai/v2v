# -*- coding: utf-8 -*-

from enum import Enum

from uutils.common import dict_to_obj


class ErrorCode(Enum):
    # 成功
    SUCCESS = 0

    # 通用错误
    ERROR_COMMON = 1
    ERROR_WORKER_SERVICE_RESET = 2
    ERROR_DISPATCH_START_MIGRATE_TIMEOUT = 4
    ERROR_DISPATCH_END_MIGRATE_TIMEOUT = 5
    ERROR_DST_VM_TYPE_INVALID = 6
    ERROR_DST_VM_VOLUME_TYPE_INVALID = 7

    # 前置检查
    PRECHECK_ERROR_COMMON = 1000
    PRECHECK_ERROR_SRC_VM_STATUS_INVALID = 1001
    PRECHECK_ERROR_OVF_COUNT_INVALID = 1002
    PRECHECK_ERROR_VMDK_COUNT_INVALID = 1003
    PRECHECK_ERROR_DST_VM_OS_TYPE_INVALID = 1004
    PRECHECK_ERROR_DST_VM_BOOT_LOADER_TYPE_INVALID = 1005
    PRECHECK_ERROR_DST_VM_BLOCK_BUS_TYPE_INVALID = 1006
    PRECHECK_ERROR_DST_VM_NET_TYPE_INVALID = 1007
    PRECHECK_ERROR_DST_VM_MEMORY_VALUE_INVALID = 1008
    PRECHECK_ERROR_DST_VM_CPU_VALUE_INVALID = 1009
    PRECHECK_ERROR_STC_VM_NFS_PATH_EMPTY = 1010

    # 导出镜像
    EXPORT_IMAGE_ERROR_COMMON = 2000
    EXPORT_IMAGE_ERROR_OVA_NOT_EXISTS = 2001

    # 上传镜像
    UPLOAD_IMAGE_ERROR_COMMON = 3000

    # 处理镜像
    DEAL_IMAGE_ERROR_COMMON = 4000
    DEAL_IMAGE_ERROR_MF_NOT_EXISTS = 4001
    DEAL_IMAGE_ERROR_OVF_NOT_MATCH = 4002
    DEAL_IMAGE_ERROR_VMDK_NOT_MATCH = 4003
    DEAL_IMAGE_ERROR_DISK_CONFIG_RELATE_IMAGE_PATH = 4004
    DEAL_IMAGE_ERROR_UNCOMPRESS_IMAGE_FAILED = 4005
    CONVERT_IMAGE_ERROR_COMMON = 5000
    CONVERT_IMAGE_ERROR_IDENTIFY_OS_DISK_FAILED = 5001
    CONVERT_IMAGE_ERROR_OS_DISK_NOT_EXISTS = 5002
    CONVERT_IMAGE_ERROR_MULTI_OS_DISK_EXISTS = 5003

    # 创建虚拟机
    REGISTER_IMAGE_ERROR_COMMON = 6000
    REGISTER_IMAGE_ERROR_UNKNOWN_VM_TYPE = 6001
    CREATE_INSTANCE_ERROR_COMMON = 7000
    CREATE_INSTANCE_ERROR_RUN_INSTANCE_FAILED = 7001
    CREATE_INSTANCE_ERROR_UPDATE_USER_QUOTAS_FAILED = 7002
    CREATE_INSTANCE_ERROR_DESCRIBE_INSTANCE_FAILED = 7003
    CREATE_INSTANCE_ERROR_START_INSTANCE_FAILED = 7004
    CREATE_INSTANCE_ERROR_STOP_INSTANCE_FAILED = 7005
    CREATE_INSTANCE_ERROR_CREATE_VOLUMES_FAILED = 7006
    CREATE_INSTANCE_ERROR_ATTACH_VOLUMES_FAILED = 7007
    CREATE_INSTANCE_ERROR_COVER_IMAGES_TO_VOLUMES_FAILED = 7008
    CREATE_INSTANCE_ERROR_UPDATE_IMAGE_STATUS_FAILED = 7009
    CREATE_INSTANCE_ERROR_START_INSTANCE_TIMEOUT = 7010
    CREATE_INSTANCE_ERROR_STOP_INSTANCE_TIMEOUT = 7011
    CREATE_INSTANCE_ERROR_VOLUME_NOT_EXISTS = 7012
    CREATE_INSTANCE_ERROR_RESTART_INSTANCE_FAILED = 7013
    CREATE_INSTANCE_ERROR_COPY_IMAGE_TO_SEED_FAILED = 7014

    # 覆盖镜像
    COVER_IMAGE_ERROR_COMMON = 8000

    # 修复调优
    RECORRECT_AND_OPTIMIZE_ERROR_COMMON = 9000


class ErrorMsg(Enum):
    # 成功
    SUCCESS = dict_to_obj(dict(en=u"", zh=u""))

    # 通用错误
    ERROR_COMMON = dict_to_obj(dict(en=u"common error", zh=u"程序通用错误"))
    ERROR_WORKER_SERVICE_RESET = dict_to_obj(dict(en=u"worker service reset", zh=u"迁移服务被重置"))
    ERROR_DISPATCH_START_MIGRATE_TIMEOUT = dict_to_obj(dict(en=u"dispatch start migrate timeout", zh=u"调度开始迁移超时"))
    ERROR_DISPATCH_END_MIGRATE_TIMEOUT = dict_to_obj(dict(en=u"dispatch end migrate timeout", zh=u"调度结束迁移超时"))
    ERROR_DST_VM_TYPE_INVALID = dict_to_obj(dict(en=u"dst vm type invalid", zh=u"目标虚拟机类型非法"))
    ERROR_DST_VM_VOLUME_TYPE_INVALID = dict_to_obj(dict(en=u"dst vm volume type invalid", zh=u"目标虚拟机硬盘类型非法"))

    # 前置检查
    PRECHECK_ERROR_COMMON = dict_to_obj(dict(en=u"migrate precheck failed", zh=u"迁移前的前置检查失败"))
    PRECHECK_ERROR_SRC_VM_STATUS_INVALID = dict_to_obj(dict(en=u"src vm status invalid", zh=u"源虚拟机的状态非法"))
    PRECHECK_ERROR_OVF_COUNT_INVALID = dict_to_obj(dict(en=u"ovf file count invalid", zh=u"OVF文件数量非法"))
    PRECHECK_ERROR_VMDK_COUNT_INVALID = dict_to_obj(dict(en=u"vmdk file count invalid", zh=u"VMDK文件数量非法"))
    PRECHECK_ERROR_DST_VM_OS_TYPE_INVALID = dict_to_obj(dict(en=u"dst vm os type invalid", zh=u"目标云服务器操作系统类型非法"))
    PRECHECK_ERROR_DST_VM_BOOT_LOADER_TYPE_INVALID = dict_to_obj(dict(en=u"dst vm boot loader type invalid", zh=u"目标云服务器引导方式非法"))
    PRECHECK_ERROR_DST_VM_BLOCK_BUS_TYPE_INVALID = dict_to_obj(dict(en=u"dst vm block bus type invalid", zh=u"目标云服务器控制器类型非法"))
    PRECHECK_ERROR_DST_VM_NET_TYPE_INVALID = dict_to_obj(dict(en=u"dst vm net type invalid", zh=u"目标云服务器网卡类型非法"))
    PRECHECK_ERROR_DST_VM_MEMORY_VALUE_INVALID = dict_to_obj(dict(en=u"dst vm memory value invalid", zh=u"目标云服务器内存数值非法"))
    PRECHECK_ERROR_DST_VM_CPU_VALUE_INVALID = dict_to_obj(dict(en=u"dst vm cpu value invalid", zh=u"目标云服务器CPU核心数非法"))
    PRECHECK_ERROR_STC_VM_NFS_PATH_EMPTY = dict_to_obj(dict(en=u"src vm nfs path empty", zh=u"源虚拟机nas存储路径为空"))

    # 导出镜像
    EXPORT_IMAGE_ERROR_COMMON = dict_to_obj(dict(en=u"export image failed", zh=u"导出镜像失败"))
    EXPORT_IMAGE_ERROR_OVA_NOT_EXISTS = dict_to_obj(dict(en=u"ova file not exists", zh=u"OVA文件不存在"))

    # 上传镜像
    UPLOAD_IMAGE_ERROR_COMMON = dict_to_obj(dict(en=u"upload image failed", zh=u"上传镜像失败"))

    # 处理镜像
    DEAL_IMAGE_ERROR_COMMON = dict_to_obj(dict(en=u"deal image failed", zh=u"处理镜像失败"))
    DEAL_IMAGE_ERROR_MF_NOT_EXISTS = dict_to_obj(dict(en=u"mf file not exists", zh=u"MF文件不存在"))
    DEAL_IMAGE_ERROR_OVF_NOT_MATCH = dict_to_obj(dict(en=u"ovf file not match", zh=u"OVF文件不匹配"))
    DEAL_IMAGE_ERROR_VMDK_NOT_MATCH = dict_to_obj(dict(en=u"vmdk file not match", zh=u"VMDK文件不匹配"))
    DEAL_IMAGE_ERROR_DISK_CONFIG_RELATE_IMAGE_PATH = dict_to_obj(dict(en=u"disk config relate image path failed", zh=u"磁盘配置关联镜像地址失败"))
    DEAL_IMAGE_ERROR_UNCOMPRESS_IMAGE_FAILED = dict_to_obj(dict(en=u"uncompress image failed", zh=u"解压镜像失败"))
    CONVERT_IMAGE_ERROR_COMMON = dict_to_obj(dict(en=u"convert image failed", zh=u"转换镜像失败"))
    CONVERT_IMAGE_ERROR_IDENTIFY_OS_DISK_FAILED = dict_to_obj(dict(en=u"identify os disk failed", zh=u"识别系统盘失败"))
    CONVERT_IMAGE_ERROR_OS_DISK_NOT_EXISTS = dict_to_obj(dict(en=u"os disk not exists", zh=u"虚拟机系统盘不存在"))
    CONVERT_IMAGE_ERROR_MULTI_OS_DISK_EXISTS = dict_to_obj(dict(en=u"multi os disk exists", zh=u"虚拟机存在多个系统盘"))

    # 创建虚拟机
    REGISTER_IMAGE_ERROR_COMMON = dict_to_obj(dict(en=u"register image failed", zh=u"注册镜像失败"))
    REGISTER_IMAGE_ERROR_UNKNOWN_VM_TYPE = dict_to_obj(dict(en=u"unknown dst vm type", zh=u"未知的目标虚拟机类型"))
    CREATE_INSTANCE_ERROR_COMMON = dict_to_obj(dict(en=u"create instance failed", zh=u"创建虚拟机失败"))
    CREATE_INSTANCE_ERROR_RUN_INSTANCE_FAILED = dict_to_obj(dict(en=u"run instance failed", zh=u"创建虚拟机失败"))
    CREATE_INSTANCE_ERROR_UPDATE_USER_QUOTAS_FAILED = dict_to_obj(dict(en=u"update user quotas failed", zh=u"更新用户配额失败"))
    CREATE_INSTANCE_ERROR_DESCRIBE_INSTANCE_FAILED = dict_to_obj(dict(en=u"describe instance failed", zh=u"获取虚拟机详情失败"))
    CREATE_INSTANCE_ERROR_START_INSTANCE_FAILED = dict_to_obj(dict(en=u"start instance failed", zh=u"启动虚拟机失败"))
    CREATE_INSTANCE_ERROR_STOP_INSTANCE_FAILED = dict_to_obj(dict(en=u"stop instance failed", zh=u"关闭虚拟机失败"))
    CREATE_INSTANCE_ERROR_CREATE_VOLUMES_FAILED = dict_to_obj(dict(en=u"create volumes failed", zh=u"创建硬盘失败"))
    CREATE_INSTANCE_ERROR_ATTACH_VOLUMES_FAILED = dict_to_obj(dict(en=u"attach volumes failed", zh=u"加载硬盘失败"))
    CREATE_INSTANCE_ERROR_COVER_IMAGES_TO_VOLUMES_FAILED = dict_to_obj(dict(en=u"cover images to volumes failed", zh=u"覆盖硬盘数据失败"))
    CREATE_INSTANCE_ERROR_UPDATE_IMAGE_STATUS_FAILED = dict_to_obj(dict(en=u"update image status failed", zh=u"更新镜像状态失败"))
    CREATE_INSTANCE_ERROR_START_INSTANCE_TIMEOUT = dict_to_obj(dict(en=u"start instance timeout", zh=u"启动虚拟机超时"))
    CREATE_INSTANCE_ERROR_STOP_INSTANCE_TIMEOUT = dict_to_obj(dict(en=u"stop instance failed", zh=u"关闭虚拟机超时"))
    CREATE_INSTANCE_ERROR_VOLUME_NOT_EXISTS = dict_to_obj(dict(en=u"volume file not exists", zh=u"硬盘文件不存在"))
    CREATE_INSTANCE_ERROR_RESTART_INSTANCE_FAILED = dict_to_obj(dict(en=u"restart instance failed", zh=u"重启虚拟机失败"))
    CREATE_INSTANCE_ERROR_COPY_IMAGE_TO_SEED_FAILED = dict_to_obj(dict(en=u"copy image to seed failed", zh=u"拷贝镜像到seed节点失败"))

    # 覆盖镜像
    COVER_IMAGE_ERROR_COMMON = dict_to_obj(dict(en=u"cover image failed", zh=u"覆盖镜像失败"))

    # 修复调优
    RECORRECT_AND_OPTIMIZE_ERROR_COMMON = dict_to_obj(dict(en=u"recorrect and optimize failed", zh=u"修复调优失败"))
