# -*- coding: utf-8 -*-

"""功能：VMware vSphere的常量定义"""

from enum import Enum


TIMEOUT_CONNECT_TO_VMWARE_VSPHERE = 200


class SrcPlatformNotConnectReason(Enum):
    """源平台无法连接的原因"""
    NET_ERROR = "net_error"
    COMMON_ERROR = "common_error"


# vsphere虚拟机状态枚举
class SrcVmStatus(Enum):
    POWEREDON = "poweredOn"
    POWEREDOFF = "poweredOff"
    SUSPENDED = "suspended"
