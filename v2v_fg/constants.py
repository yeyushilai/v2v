# -*- coding: utf-8 -*-

from enum import Enum

from zk.constants import QUEUE_HOME_PATH
from utils.yaml_tool import yaml_load
from api.constants import (
    # 虚拟机（云服务器）类型
    INSTANCE_CLASS_HIGH_PERFORMANCE,
    INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS,
    INSTANCE_CLASS_SAN_CONTAINER,
    INSTANCE_CLASS_HIGH_CAPACITY_SAN,
    INSTANCE_CLASS_S1,
    INSTANCE_CLASS_E1,
    INSTANCE_CLASS_E2,
    INSTANCE_CLASS_E3,
    INSTANCE_CLASS_P1,

    # 本地盘
    VOLUME_TYPE_HIGH_PERFORMANCE,
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS,
    VOLUME_TYPE_ST,
    VOLUME_TYPE_ET,

    # 云盘
    VOLUME_TYPE_HIGH_CAPACITY,
    VOLUME_TYPE_HIGH_CAPACITY_PLUS,
    VOLUME_TYPE_HIGH_CAPACITY_SAN,
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED,
)


class CommonEnum(Enum):

    @classmethod
    def list_type(cls):
        type_list = []
        for element in cls.__members__.keys():
            single_type = getattr(cls, element).value
            type_list.append(single_type)
        return type_list


# ---------------------------------------------
#       framework
# ---------------------------------------------
# v2v Job queue name
ACTION_REDIRECT_TO_WS = "RedirectToWebService"


# ---------------------------------------------
#       The constants for api action
# ---------------------------------------------
# 健康检查
ACTION_V2V_HEALTH_HEALTH_CHECK = "V2VMigrationTaskHealthCheck"

# NAS（NFS）管理
ACTION_V2V_NAS_CHECK_NAS_CONNECTIVITY = "V2VNasCheckNasConnectivity"
ACTION_V2V_NAS_PARSE_VMS_FROM_NAS = "V2VNasParseVmsFromNas"

# 源平台管理
ACTION_V2V_SRC_PLATFORM_CHECK_SRC_PLATFORM_CONNECTIVITY = "V2VSrcPlatformCheckSrcPlatformConnectivity"
ACTION_V2V_SRC_PLATFORM_ADD_SRC_PLATFORM = "V2VSrcPlatformAddSrcPlatform"
ACTION_V2V_SRC_PLATFORM_UPDATE_SRC_PLATFORM = "V2VSrcPlatformUpdateSrcPlatform"
ACTION_V2V_SRC_PLATFORM_DELETE_SRC_PLATFORM = "V2VSrcPlatformDeleteSrcPlatform"
ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM = "V2VSrcPlatformDescribeSrcPlatform"
ACTION_V2V_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM = "V2VSrcPlatformDescribeSrcPlatformVm"

# IAAS管理
ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES = "V2VIaasDescribeIaasHyperNodes"
ACTION_V2V_IAAS_DESCRIBE_IAAS_HYPER_NODES_PG_RULE = "V2VIaasDescribeIaasHyperNodesPGRule"

# 迁移任务管理
ACTION_V2V_MIGRATION_TASK_CREATE_MIGRATION_TASK = "V2VMigrationTaskCreateMigrationTask"
ACTION_V2V_MIGRATION_TASK_UPDATE_MIGRATION_TASK = "V2VMigrationTaskUpdateMigrationTask"
ACTION_V2V_MIGRATION_TASK_DELETE_MIGRATION_TASK = "V2VMigrationTaskDeleteMigrationTask"
ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_TASK = "V2VMigrationTaskDescribeMigrationTask"
ACTION_V2V_MIGRATION_TASK_DETAIL_MIGRATION_TASK = "V2VMigrationTaskDetailMigrationTask"
ACTION_V2V_MIGRATION_TASK_DESCRIBE_MIGRATION_VM = "V2VMigrationTaskDescribeMigrationVm"

# 迁移虚拟机管理
ACTION_V2V_MIGRATION_VM_UPDATE_VM = "V2VMigrationVmUpdateVm"
ACTION_V2V_MIGRATION_VM_DELETE_VM = "V2VMigrationVmDeleteVm"
ACTION_V2V_MIGRATION_VM_OPERATE_VM = "V2VMigrationVmOperateVm"

# IAAS api action
DESC_INSTANCES = "DescribeInstances"
GET_MONITOR = "GetMonitor"
DESC_CLUSTER_USERS = "DescribeClusterUsers"
DESC_CLUSTER = "DescribeClusters"
GET_USER_CLUSTER_COUNT = "GetUserClusterCount"
DESC_USERS = "DescribeUsers"
DESC_SWITCHES = "DescribeSwitches"
GET_CHARGE_SUMS = "GetChargeSums"
DESC_VOLUMES = "DescribeVolumes"
GET_BUCKETS = "buckets-list"
DESC_ACCESS_KEYS = "DescribeAccessKeys"
DESC_S2SERVERS = "DescribeS2Servers"
DESC_S2SHARDTARGETS = "DescribeS2SharedTargets"
DESC_BOTS = "DescribeBots"
DESC_QUOTAS = "DescribeQuotas"
DESC_VXNETS = "DescribeVxnets"
GET_QUOTA_LEFT = "GetQuotaLeft"
DESC_PLG = "DescribePlaceGroups"
DESC_PLG_RULE = "DescribePlaceGroupRules"


# ---------------------------------------------
#       table job
# ---------------------------------------------
TB_JOB = "v2v"

# timeout for push event
TIMEOUT_PUSH_EVENT = 5
# timeout for vmware_vsphere
# TIMEOUT_CONNECT_TO_VMWARE_VSPHERE = 200

# pull server tasks
TASK_ACTION_UPDATE_RESOURCE_LEASING = "UpdateResourceLeasing"

# long handle time
LONG_HANDLE_TIME = 30

V2V_JOB_QUEUE_PATH = QUEUE_HOME_PATH + "/v2v_job"


# -----------------------------------------------------------------------------
#       src platform
# -----------------------------------------------------------------------------
class SrcPlatformType(Enum):
    """源平台类型"""
    VMWARE = "vmware"
    KVM = "kvm"  # 目前暂不支持


class SrcPlatformStatus(Enum):
    """源平台类型"""
    MIGRATE_SUPPORT = "migrate_support"
    MIGRATE_NOT_SUPPORT = "migrate_not_support"


CONNECTION_STATUS_MAPPER = {
    True: SrcPlatformStatus.MIGRATE_SUPPORT.value,
    False: SrcPlatformStatus.MIGRATE_NOT_SUPPORT.value
}


class SrcPlatformVmStatus(Enum):
    """源平台虚拟机状态"""
    POWEREDON = "poweredOn"
    POWEREDOFF = "poweredOff"
    SUSPENDED = "suspended"


# -----------------------------------------------------------------------------
#       migration
# -----------------------------------------------------------------------------
class MigrateStatus(CommonEnum):
    """迁移状态"""
    READY = "ready"
    QUEUING = "queuing"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def list_waiting_migrate_status(cls):
        return [cls.QUEUING.value, cls.PENDING.value]

    @classmethod
    def list_support_delete_status(cls):
        return [cls.FAILED.value, cls.COMPLETED.value, cls.READY.value]

    @classmethod
    def list_schedulable_migrate_status(cls):
        return [cls.READY.value, cls.FAILED.value]

    @classmethod
    def list_processing_migrate_status(cls):
        return [cls.RUNNING.value]


# -----------------------------------------------------------------------------
#       zk
# -----------------------------------------------------------------------------
V2V_ZK_HYPER_PATH = "/v2v_worker"

# zookeeper服务全局配置
ZOOKEEPER_CONF_FILE_PATH = "/pitrix/conf/global/zookeeper.yaml"
with open(ZOOKEEPER_CONF_FILE_PATH, "r") as f:
    ZOOKEEPER_CONF = yaml_load(f)


# -----------------------------------------------------------------------------
#       redis
# -----------------------------------------------------------------------------
REDIS_CONFIG_NAME_V2V = "v2v"


# -----------------------------------------------------------------------------
#       instance
# -----------------------------------------------------------------------------
class InstanceOSType(CommonEnum):
    """云服务器（虚拟机）操作系统类型"""
    WINDOWS = "windows"
    CENTOS = "centos"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    SUSE = "suse"
    REDHAT = "redhat"
    OPENSUSE = "opensuse"
    COREOS = "coreos"
    FEDORA = "fedora"
    DESKTOP = "desktop"
    FREEBSD = "freebsd"
    ARCH = "arch"
    ORACLE = "oracle"

    @classmethod
    def list_linux_type(cls):
        return [cls.CENTOS.value, cls.DEBIAN.value, cls.UBUNTU.value,
                cls.SUSE.value, cls.REDHAT.value, cls.OPENSUSE.value,
                cls.COREOS.value, cls.FEDORA.value, cls.DESKTOP.value,
                cls.FREEBSD.value, cls.ARCH.value, cls.ORACLE.value]


class InstanceBootLoaderType(CommonEnum):
    """云服务器（虚拟机）启动类型"""
    OTHER = "other"
    UEFI = "uefi"
    AUTO = "auto"


# 启动类型和枚举值的映射
INSTANCE_BOOT_LOADER_MAPPER = {
    InstanceBootLoaderType.OTHER.value: "",
    InstanceBootLoaderType.UEFI.value: "OVMF-20160813.fd",
    InstanceBootLoaderType.AUTO.value: ""
}


# 内存类型
# 单位为MB
INSTANCE_MEMORY_TYPE = [
    1024,       # 1GB
    2048,       # 2GB
    3072,       # 3GB
    4096,       # 4GB
    5120,       # 5GB
    6144,       # 6GB
    8192,       # 8GB
    10240,      # 10GB
    11264,      # 11GB
    12288,      # 12GB
    16384,      # 16GB
    20480,      # 20GB
    24576,      # 24GB
    32768,      # 32GB
    40960,      # 40GB
    49152,      # 48GB
    61440,      # 60GB
    65536,      # 64GB
    67584,      # 66GB
    81920,      # 80GB
    98304,      # 96GB
    102400,     # 100GB
    114688,     # 112GB
    122880,     # 120GB
    128000,     # 125GB
    131072,     # 128GB
    163840,     # 160GB
    196608,     # 192GB
    229376,     # 224GB?
    245760,     # 240GB
    262144,     # 256GB
    327680,     # 320GB?
    360448,     # 352GB
    393216,     # 384GB
    409600,     # 400GB
    458752,     # 448GB
    471040,     # 460GB
    491520,     # 480GB
    524288,     # 512GB
    4194304,    # 4096GB
]


# CPU类型
# 单位为核心数
INSTANCE_CPU_TYPE = [1, 2, 4, 8, 10, 12, 14, 16, 24, 26, 32, 40, 48, 52, 54, 56, 62, 64, 92, 96, 100, 120, 124, 128]

# 虚拟机类型枚举值
"""
# 性能型
INSTANCE_CLASS_HIGH_PERFORMANCE = 0

# 超高性能型
INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS = 1

# SAN存储超高性能型
INSTANCE_CLASS_SAN_CONTAINER = 6

# SAN存储性能型
INSTANCE_CLASS_HIGH_CAPACITY_SAN = 7

# 基础型s1
INSTANCE_CLASS_S1 = 101

# 企业型e1
INSTANCE_CLASS_E1 = 201

# 企业型e2(包括新版的计算型(1:1/1:2)通用型(1:4)内存型(1:8))
INSTANCE_CLASS_E2 = 202

# 企业型e3(包括新版的计算型(1:1/1:2)通用型(1:4)内存型(1:8))
INSTANCE_CLASS_E3 = 203

# 专业增强型p1
INSTANCE_CLASS_P1 = 301
"""

# 虚拟机类型枚举值和虚拟机类型的映射
QUOTA_INSTANCE_ENUM_AND_TYPE_MAP = {
    INSTANCE_CLASS_HIGH_PERFORMANCE: "instance",
    INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS: "hp_instance",

    INSTANCE_CLASS_SAN_CONTAINER: "hps_instance",
    INSTANCE_CLASS_HIGH_CAPACITY_SAN: "hcs_instance",

    INSTANCE_CLASS_S1: "st_instance",

    INSTANCE_CLASS_E1: "et_instance",
    INSTANCE_CLASS_E2: "et_instance",
    INSTANCE_CLASS_E3: "et_instance",

    INSTANCE_CLASS_P1: "pt_instance"
}

# 虚拟机类型枚举值和虚拟机内存类型的映射
QUOTA_INSTANCE_ENUM_AND_MEMORY_TYPE_MAP = {
    INSTANCE_CLASS_HIGH_PERFORMANCE: "memory",
    INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS: "hp_memory",

    INSTANCE_CLASS_SAN_CONTAINER: "hps_memory",
    INSTANCE_CLASS_HIGH_CAPACITY_SAN: "hcs_memory",

    INSTANCE_CLASS_S1: "st_memory",

    INSTANCE_CLASS_E1: "et_memory",
    INSTANCE_CLASS_E2: "et_memory",
    INSTANCE_CLASS_E3: "et_memory",

    INSTANCE_CLASS_P1: "pt_memory"
}

# 虚拟机类型枚举值和虚拟机CPU类型的映射
QUOTA_INSTANCE_ENUM_AND_CPU_TYPE_MAP = {
    INSTANCE_CLASS_HIGH_PERFORMANCE: "cpu",
    INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS: "hp_cpu",

    INSTANCE_CLASS_SAN_CONTAINER: "hps_cpu",
    INSTANCE_CLASS_HIGH_CAPACITY_SAN: "hcs_cpu",

    INSTANCE_CLASS_S1: "st_cpu",

    INSTANCE_CLASS_E1: "et_cpu",
    INSTANCE_CLASS_E2: "et_cpu",
    INSTANCE_CLASS_E3: "et_cpu",

    INSTANCE_CLASS_P1: "pt_cpu"
}

# 硬盘类型枚举值
"""
# 性能型本地盘
VOLUME_TYPE_HIGH_PERFORMANCE = 0

# 超高性能型本地盘
VOLUME_TYPE_HIGH_PERFORMANCE_PLUS = 3

# 基础型本地盘
VOLUME_TYPE_ST = 100

# 企业级SSD本地盘
VOLUME_TYPE_ET = 200

# 容量型云盘-----已经下架
VOLUME_TYPE_HIGH_CAPACITY = 1

# 容量型云盘
VOLUME_TYPE_HIGH_CAPACITY_PLUS = 2

# SAN-----已经下架
VOLUME_TYPE_SAN = 4

# SAN容量型云盘
# hdd
VOLUME_TYPE_HIGH_CAPACITY_SAN = 6

# 企业级分布式云盘 (NeonSAN)-----个人理解就是SAN性能型云盘
# ssd
VOLUME_TYPE_HIGH_PERFORMANCE_SHARED = 5

# 增强型SSD云盘
VOLUME_TYPE_RDMA_SAN = 7

"""

# 硬盘类型枚举值和硬盘类型名称的映射
QUOTA_VOLUME_ENUM_AND_NAME_MAP = {
    VOLUME_TYPE_HIGH_PERFORMANCE: "volume",
    VOLUME_TYPE_HIGH_CAPACITY: "hc_volume",
    VOLUME_TYPE_HIGH_CAPACITY_PLUS: "hc_volume",
    VOLUME_TYPE_HIGH_CAPACITY_SAN: "hcs_volume",
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS: "hpp_volume",
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED: "hps_volume",
    VOLUME_TYPE_ST: "st_volume",
    VOLUME_TYPE_ET: "et_volume"
}

# 硬盘类型枚举值和硬盘类型大小名称的映射
QUOTA_VOLUME_ENUM_AND_SIZE_MAP = {
    VOLUME_TYPE_HIGH_PERFORMANCE: "volume_size",
    VOLUME_TYPE_HIGH_CAPACITY: "hc_volume_size",
    VOLUME_TYPE_HIGH_CAPACITY_PLUS: "hc_volume_size",
    VOLUME_TYPE_HIGH_CAPACITY_SAN: "hcs_volume_size",
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS: "hpp_volume_size",
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED: "hps_volume_size",
    VOLUME_TYPE_ST: "st_volume_size",
    VOLUME_TYPE_ET: "et_volume_size"
}
