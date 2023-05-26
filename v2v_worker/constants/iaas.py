# -*- coding: utf-8 -*-

from enum import Enum
from utils.yaml_tool import yaml_load
from utils.pitrix_folder import PitrixFolder
from api.constants import (
    # 虚拟机类型
    INSTANCE_CLASS_HIGH_PERFORMANCE,
    INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS,
    INSTANCE_CLASS_SAN_CONTAINER,
    INSTANCE_CLASS_HIGH_CAPACITY_SAN,
    INSTANCE_CLASS_S1,
    INSTANCE_CLASS_E1,
    INSTANCE_CLASS_E2,
    INSTANCE_CLASS_E3,
    INSTANCE_CLASS_P1,

    # 磁盘类型
    VOLUME_TYPE_HIGH_PERFORMANCE,
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS,
    VOLUME_TYPE_ST,
    VOLUME_TYPE_ET,
    VOLUME_TYPE_HIGH_CAPACITY_PLUS,
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED,
    VOLUME_TYPE_HIGH_CAPACITY_SAN
)


class CommonEnum(Enum):

    @classmethod
    def list_type(cls):
        type_list = []
        for element in cls.__members__.keys():
            single_type = getattr(cls, element).value
            type_list.append(single_type)
        return type_list


class QemuImgAction(Enum):
    """QemuImg动作"""
    CONVERT = "convert"


# server服务全局配置
SERVER_CONF_FILE_PATH = PitrixFolder.CONF_HOME + "/global/server.yaml"
with open(SERVER_CONF_FILE_PATH, "r") as f:
    SERVER_CONF = yaml_load(f)


class HyperContainerMode(Enum):
    """存储部署模式（容器模式）"""
    REPL = "repl"
    PAIR = "pair"
    SANC = "sanc"
    NASC = "nasc"
    LOCAL = "local"


# hyper存储模式数据库值和页面值的映射
HYPER_CONTAINER_MODE_MAPPER = {
    HyperContainerMode.PAIR.value: "SDS 1.0",                    # drbd
    HyperContainerMode.REPL.value: "SDS 2.0",                    # zfs
    HyperContainerMode.SANC.value: "NeonSAN Container 模式",     #
    HyperContainerMode.NASC.value: "NAS 模式",                   # nas
    HyperContainerMode.LOCAL.value: "本地模式",
}


# hyper节点相关常量
HYPER_IMAGE_BASE_DIR = "/pitrix/data/container"
HYPER_ID_RSA_PATH = "/root/.ssh/id_rsa"
HYPER_VMWARE_OVF_TOOL_PATH = "/usr/bin/ovftool"     # VMware OVF Tool工具
HYPER_QEMU_IMG_TOOL_PATH = "/usr/bin/qemu-img"      # Qemu-img Tool工具
HYPER_DEFAULT_USER = "root"

# seed节点相关常量
SEED_IMAGE_REPOSITORY_BASE_DIR = "/pitrix/images-repo"
SEED_ID_RSA_PATH = "/root/.ssh/id_rsa"
SEED_DEFAULT_USER = "root"
SEED_NODES = SERVER_CONF['common']['image_sources'].split(',')


class ImageStatus(Enum):
    """镜像状态"""
    DEPRECATED = "deprecated"   # 已被弃用，此时不再可以基于该镜像创建新的云服务器，但不影响已有云服务器的正常使用。
    AVAILABLE = "available"     # 可用状态，此时可以基于该镜像创建云服务器
    CEASED = "ceased"           # 已被彻底删除，处于此状态的镜像无法恢复


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
    LEGACY = ""
    UEFI = "uefi"
    AUTO = "auto"


# 启动类型和枚举值的映射
INSTANCE_BOOT_LOADER_MAPPER = {
    InstanceBootLoaderType.LEGACY.value: "",
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


class SupportInstanceType(CommonEnum):
    """支持的虚拟机类型枚举"""
    INSTANCE_CLASS_HIGH_PERFORMANCE = INSTANCE_CLASS_HIGH_PERFORMANCE
    INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS = INSTANCE_CLASS_HIGH_PERFORMANCE_PLUS
    INSTANCE_CLASS_SAN_CONTAINER = INSTANCE_CLASS_SAN_CONTAINER
    INSTANCE_CLASS_HIGH_CAPACITY_SAN = INSTANCE_CLASS_HIGH_CAPACITY_SAN
    INSTANCE_CLASS_S1 = INSTANCE_CLASS_S1
    INSTANCE_CLASS_E1 = INSTANCE_CLASS_E1
    INSTANCE_CLASS_E2 = INSTANCE_CLASS_E2
    INSTANCE_CLASS_E3 = INSTANCE_CLASS_E3
    INSTANCE_CLASS_P1 = INSTANCE_CLASS_P1


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
# 原名：性能型
VOLUME_TYPE_HIGH_PERFORMANCE = 0

# 容量型云盘
# 原名：容量型
VOLUME_TYPE_HIGH_CAPACITY_PLUS = 2

# 超高性能型本地盘
# 原名：超高性能型
VOLUME_TYPE_HIGH_PERFORMANCE_PLUS = 3

# 通用型SSD云盘
# 别名：企业级分布式云盘 (NeonSAN)，个人理解就是SAN性能型云盘
# 原名：企业级分布式SAN
# ssd
VOLUME_TYPE_HIGH_PERFORMANCE_SHARED = 5

# 容量型云盘
# 别名：SAN容量型云盘
# 原名：容量型
# hdd
VOLUME_TYPE_HIGH_CAPACITY_SAN = 6

# 基础型本地盘
# 原名：基础型
VOLUME_TYPE_ST = 100

# 企业型SSD本地盘
# 原名：SSD企业级
VOLUME_TYPE_ET = 200
"""


class SupportVolumeType(CommonEnum):
    """支持的硬盘类型枚举"""
    VOLUME_TYPE_HIGH_PERFORMANCE = VOLUME_TYPE_HIGH_PERFORMANCE                 # 0
    VOLUME_TYPE_HIGH_CAPACITY_PLUS = VOLUME_TYPE_HIGH_CAPACITY_PLUS             # 2
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS = VOLUME_TYPE_HIGH_PERFORMANCE_PLUS       # 3
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED = VOLUME_TYPE_HIGH_PERFORMANCE_SHARED   # 5
    VOLUME_TYPE_HIGH_CAPACITY_SAN = VOLUME_TYPE_HIGH_CAPACITY_SAN               # 6
    VOLUME_TYPE_ST = VOLUME_TYPE_ST                                             # 100
    VOLUME_TYPE_ET = VOLUME_TYPE_ET                                             # 200


class LocalVolumeType(CommonEnum):
    """本地盘类型枚举"""
    VOLUME_TYPE_HIGH_PERFORMANCE = VOLUME_TYPE_HIGH_PERFORMANCE             # 0
    VOLUME_TYPE_HIGH_CAPACITY_PLUS = VOLUME_TYPE_HIGH_CAPACITY_PLUS         # 2
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS = VOLUME_TYPE_HIGH_PERFORMANCE_PLUS   # 3
    VOLUME_TYPE_ST = VOLUME_TYPE_ST                                         # 100
    VOLUME_TYPE_ET = VOLUME_TYPE_ET                                         # 200


class SANCVolumeType(CommonEnum):
    """NeonSAN类型枚举"""
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED = VOLUME_TYPE_HIGH_PERFORMANCE_SHARED   # 5
    VOLUME_TYPE_HIGH_CAPACITY_SAN = VOLUME_TYPE_HIGH_CAPACITY_SAN               # 6


# 硬盘类型枚举值和硬盘类型名称的映射
QUOTA_VOLUME_ENUM_AND_NAME_MAP = {
    VOLUME_TYPE_HIGH_PERFORMANCE: "volume",
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
    VOLUME_TYPE_HIGH_CAPACITY_PLUS: "hc_volume_size",
    VOLUME_TYPE_HIGH_CAPACITY_SAN: "hcs_volume_size",
    VOLUME_TYPE_HIGH_PERFORMANCE_PLUS: "hpp_volume_size",
    VOLUME_TYPE_HIGH_PERFORMANCE_SHARED: "hps_volume_size",
    VOLUME_TYPE_ST: "st_volume_size",
    VOLUME_TYPE_ET: "et_volume_size"
}
