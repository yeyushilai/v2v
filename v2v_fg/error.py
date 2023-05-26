# -*- coding: utf-8 -*-

from enum import Enum


from api.constants import (
    EN,
    ZH_CN,
    DEFAULT_LANG,
    SUPPORTED_LANGS
)


class Error(object):
    """ error class """

    def __init__(self, code, message, *args, **kwargs):
        """
        @param code - the error code, it is an integer.
        @param message - the error message to describe the error information in detail.
                         it is a dict with multi-language defined
        """
        self._code = code
        self._message = message
        self._args = args
        self._kwargs = kwargs

    def format_args(self):
        if isinstance(self._args, (int, long, float, bool)):
            return self._args

        # case 2, non unicode characters
        try:
            return str(self._args).decode('utf-8')
        except Exception:
            pass

        # case 3, it comes from the API parameter passed by the user
        return "%s" % self._args

    @property
    def code(self):
        """ return a valid error code that defined in error codes"""
        return self._code

    def get_message(self, lang=DEFAULT_LANG):
        lang = DEFAULT_LANG if lang not in SUPPORTED_LANGS else lang
        raw_message = self._message.get(lang)

        assert not all([self._args, self._kwargs])

        msg = raw_message
        if self._args:
            try:
                msg = raw_message % format(self.format_args())
            except:
                pass

        if self._kwargs:
            try:
                msg = raw_message.format(**self._kwargs)
            except:
                pass

        return msg


class ErrorCode(Enum):
    # 成功
    SUCCESS = 0

    # 通用错误
    ERR_CODE_COMMON = 1000
    ERR_CODE_COMMON_OPERATE_PG_ERROR = 1001
    ERR_CODE_COMMON_OPERATE_REDIS_ERROR = 1002

    # IAAS错误
    ERR_CODE_IAAS_COMMON = 2000
    ERR_CODE_IAAS_INVALID_OS_TYPE = 2001
    ERR_CODE_IAAS_INVALID_CPU_TYPE = 2002
    ERR_CODE_IAAS_INVALID_MEMORY_TYPE = 2003
    ERR_CODE_IAAS_INVALID_VOLUME_TYPE = 2004

    ERR_CODE_IAAS_HYPER_DATA_EMPTY = 2005
    ERR_CODE_IAAS_HYPER_FREE_DISK_NOT_ENOUGH = 2006
    ERR_CODE_IAAS_HYPER_FREE_MEMORY_NOT_ENOUGH = 2007
    ERR_CODE_IAAS_HYPER_FREE_CPU_NOT_ENOUGH = 2008

    ERR_CODE_IAAS_USER_QUOTA_NOT_ENOUGH = 2009

    # 迁移任务错误
    ERR_CODE_MIGRATION_TASK_COMMON = 3000
    ERR_CODE_MIGRATION_TASK_DELETE_PART_MIGRATION_TASK_ERROE = 3001
    ERR_CODE_MIGRATION_TASK_CREATE_MIGRATION_TASK_ERROE = 3002
    ERR_CODE_MIGRATION_TASK_SCHEDULER_MIGRATION_TASK_ERROE = 3003
    ERR_CODE_MIGRATION_TASK_MIGRATION_TASK_EXISTS = 3004
    ERR_CODE_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS = 3005
    ERR_CODE_MIGRATION_TASK_INCLUDED_WORKING_VM_EXISTS = 3006
    ERR_CODE_MIGRATION_TASK_INCLUDED_VM_EXISTS = 3007
    ERR_CODE_MIGRATION_TASK_INCLUDED_VM_NOT_EXISTS = 3008

    # 迁移虚拟机错误
    ERR_CODE_MIGRATION_VM_COMMON = 4000
    ERR_CODE_MIGRATION_VM_UPDATE_MIGRATION_VM_ERROR = 4001
    ERR_CODE_MIGRATION_VM_DELETE_MIGRATION_VM_ERROR = 4002
    ERR_CODE_MIGRATION_VM_INNER_IP_CONFLICTS = 4003
    ERR_CODE_MIGRATION_VM_OPERATE_PART_MIGRATION_VM_ERROE = 4004
    ERR_CODE_MIGRATION_VM_DELETE_PART_MIGRATION_VM_ERROE = 4005
    ERR_CODE_MIGRATION_VM_DELETE_RELATIVE_MIGRATION_TASK_ERROE = 4006

    # NAS错误
    ERR_CODE_NAS_COMMON = 5000
    ERR_CODE_NAS_NFS_URL_NOT_CONNECT = 5001
    ERR_CODE_NAS_NFS_URL_IP_NOT_CONNECT = 5002
    ERR_CODE_NAS_NFS_URL_PORT_NOT_CONNECT = 5003
    ERR_CODE_NAS_INVAILD_NFS_URL_ADDRESS = 5004
    ERR_CODE_NAS_PARSE_VMS_FROM_NFS_PAGINATE_ERROR = 5005

    # 源平台错误
    ERR_CODE_SRC_PLATFORM_COMMON = 6000
    ERR_CODE_SRC_PLATFORM_INVALID_SRC_PLATFORM_TYPE = 6001
    ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_EXISTS = 6002
    ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_EXISTS = 6003
    ERR_CODE_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT = 6004
    ERR_CODE_SRC_PLATFORM_LIST_VM_IN_SRC_PLATFORM_ERROR = 6005
    ERR_CODE_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM_PAGINATE_ERROR = 6006
    ERR_CODE_SRC_PLATFORM_RELATIVE_WORKING_MIGRATION_TASK_EXISTS = 6007


class ErrorMsg(Enum):
    # 成功
    SUCCESS = {
        EN: u"success",
        ZH_CN: u"成功"
    }

    # 通用错误
    ERR_MSG_COMMON = {
        EN: u"common error",
        ZH_CN: u"通用错误"
    }
    ERR_MSG_COMMON_OPERATE_PG_ERROR = {
        EN: u"operate postgresql error",
        ZH_CN: u"和数据库交互错误"
    }
    ERR_MSG_COMMON_OPERATE_REDIS_ERROR = {
        EN: u"operate redis error",
        ZH_CN: u"和数据库交互错误"
    }

    # IAAS错误
    ERR_MSG_IAAS_COMMON = {
        EN: u"iaas common error",
        ZH_CN: u"IAAS通用错误"
    }
    ERR_MSG_IAAS_INVALID_OS_TYPE = {
        EN: u"invalid os type",
        ZH_CN: u"非法的操作系统类型"
    }
    ERR_MSG_IAAS_INVALID_CPU_TYPE = {
        EN: u"invalid cpu type",
        ZH_CN: u"非法的CPU类型"
    }
    ERR_MSG_IAAS_INVALID_MEMORY_TYPE = {
        EN: u"invalid memory type",
        ZH_CN: u"非法的内存类型"
    }
    ERR_MSG_IAAS_INVALID_VOLUME_TYPE = {
        EN: u"invalid volume type",
        ZH_CN: u"非法的硬盘类型"
    }
    ERR_MSG_IAAS_HYPER_DATA_EMPTY = {
        EN: u"hyper node data is empty",
        ZH_CN: u"Hyper节点数据缺失"
    }
    ERR_MSG_IAAS_HYPER_FREE_DISK_NOT_ENOUGH = {
        EN: u"the free disk of hyper node is not enough",
        ZH_CN: u"Hyper节点的剩余硬盘空间不足"
    }
    ERR_MSG_IAAS_HYPER_FREE_MEMORY_NOT_ENOUGH = {
        EN: u"the free memory of hyper node is not enough",
        ZH_CN: u"Hyper节点的剩余内存不足"
    }
    ERR_MSG_IAAS_HYPER_FREE_CPU_NOT_ENOUGH = {
        EN: u"the free cpu of hyper node is not enough",
        ZH_CN: u"Hyper节点的剩余CPU核心数不足"
    }
    ERR_MSG_IAAS_USER_QUOTA_NOT_ENOUGH = {
        EN: u"the quota of user is not enough",
        ZH_CN: u"用户的配额不足"
    }

    # 迁移任务错误
    ERR_MSG_MIGRATION_TASK_COMMON = {
        EN: u"migration task common error",
        ZH_CN: u"迁移任务通用错误"
    }
    ERR_MSG_MIGRATION_TASK_CREATE_MIGRATION_TASK_ERROE = {
        EN: u"create migration task error",
        ZH_CN: u"创建迁移任务错误"
    }
    ERR_MSG_MIGRATION_TASK_DELETE_PART_MIGRATION_TASK_ERROE = {
        EN: u"delete part migration task error, success list: {success_list}, failed list: {failed_list}",
        ZH_CN: u"删除部分迁移任务错误，成功列表：{success_list}，失败列表：{failed_list}"
    }
    ERR_MSG_MIGRATION_TASK_SCHEDULER_MIGRATION_TASK_ERROE = {
        EN: u"scheduler migration task error",
        ZH_CN: u"调度迁移任务错误"
    }
    ERR_MSG_MIGRATION_TASK_MIGRATION_TASK_EXISTS = {
        EN: u"migration task exists",
        ZH_CN: u"迁移任务已存在"
    }
    ERR_MSG_MIGRATION_TASK_MIGRATION_TASK_NOT_EXISTS = {
        EN: u"migration task not exists",
        ZH_CN: u"迁移任务不存在"
    }
    ERR_MSG_MIGRATION_TASK_INCLUDED_WORKING_VM_EXISTS = {
        EN: u"included migrating vm exists, please wait",
        ZH_CN: u"迁移任务包含的迁移中的虚拟机存在, 请等待迁移完毕"
    }
    ERR_MSG_MIGRATION_TASK_INCLUDED_VM_EXISTS = {
        EN: u"included vm exists",
        ZH_CN: u"迁移任务包含的虚拟机存在"
    }
    ERR_MSG_MIGRATION_TASK_INCLUDED_VM_NOT_EXISTS = {
        EN: u"included vm not exists",
        ZH_CN: u"迁移任务包含的的虚拟机不存在"
    }

    # 迁移虚拟机错误
    ERR_MSG_MIGRATION_VM_COMMON = {
        EN: u"migration vm common error",
        ZH_CN: u"迁移任务中的虚拟机通用错误"
    }
    ERR_MSG_MIGRATION_VM_UPDATE_MIGRATION_VM_ERROR = {
        EN: u"update migration vm error",
        ZH_CN: u"更新迁移任务中的虚拟机错误"
    }
    ERR_MSG_MIGRATION_VM_DELETE_MIGRATION_VM_ERROR = {
        EN: u"delete migration vm error",
        ZH_CN: u"删除迁移任务中的虚拟机错误"
    }
    ERR_MSG_MIGRATION_VM_INNER_IP_CONFLICTS = {
        EN: u"inner ip of migration vm is conflicts",
        ZH_CN: u"虚拟机IP冲突"
    }
    ERR_MSG_MIGRATION_VM_OPERATE_PART_MIGRATION_VM_ERROE = {
        EN: u"operate part migration vm error, success list: {success_list}, failed list: {failed_list}",
        ZH_CN: u"操作部分虚拟机错误，成功列表：{success_list}，失败列表：{failed_list}"
    }
    ERR_MSG_MIGRATION_VM_DELETE_PART_MIGRATION_VM_ERROE = {
        EN: u"delete part migration vm error, success list: {success_list}, failed list: {failed_list}",
        ZH_CN: u"删除部分虚拟机错误，成功列表：{success_list}，失败列表：{failed_list}"
    }
    ERR_MSG_MIGRATION_VM_DELETE_RELATIVE_MIGRATION_TASK_ERROE = {
        EN: u"delete relative migration task error",
        ZH_CN: u"删除关联的迁移任务错误"
    }

    # NAS错误
    ERR_MSG_NAS_COMMON = {
        EN: u"nas common error",
        ZH_CN: u"NAS通用错误"
    }
    ERR_MSG_NAS_NFS_URL_NOT_CONNECT = {
        EN: u"nfs url not connect",
        ZH_CN: u"NFS服务地址不通"
    }
    ERR_MSG_NAS_NFS_URL_IP_NOT_CONNECT = {
        EN: u"the ip of nfs url not connect",
        ZH_CN: u"NFS服务地址主机不通"
    }
    ERR_MSG_NAS_NFS_URL_PORT_NOT_CONNECT = {
        EN: u"the port of nfs url not connect",
        ZH_CN: u"NFS服务地址端口不通"
    }
    ERR_MSG_NAS_INVAILD_NFS_URL_ADDRESS = {
        EN: u"invaild nfs url address",
        ZH_CN: u"非法的NFS服务地址"
    }
    ERR_MSG_NAS_PARSE_VMS_FROM_NFS_PAGINATE_ERROR = {
        EN: u"parse vms from nfs paginate error",
        ZH_CN: u"从NFS服务地址中解析虚拟机列表时分页错误"
    }

    # 源平台错误
    ERR_MSG_SRC_PLATFORM_COMMON = {
        EN: u"src platform common error",
        ZH_CN: u"源平台通用错误"
    }
    ERR_MSG_SRC_PLATFORM_INVALID_SRC_PLATFORM_TYPE = {
        EN: u"invalid src platform type",
        ZH_CN: u"非法的源平台类型"
    }
    ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_EXISTS = {
        EN: u"src platform not exists",
        ZH_CN: u"源平台不存在"
    }
    ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_EXISTS = {
        EN: u"src platform exists",
        ZH_CN: u"源平台已存在"
    }
    ERR_MSG_SRC_PLATFORM_SRC_PLATFORM_NOT_CONNECT = {
        EN: u"src platform not connect",
        ZH_CN: u"源平台不通"
    }
    ERR_MSG_SRC_PLATFORM_LIST_VM_IN_SRC_PLATFORM_ERROR = {
        EN: u"list vm in src platform error",
        ZH_CN: u"列举源平台中的虚拟机错误"
    }
    ERR_MSG_SRC_PLATFORM_DESCRIBE_SRC_PLATFORM_VM_PAGINATE_ERROR = {
        EN: u"describe src platform vm paginate error",
        ZH_CN: u"列举源平台中的虚拟机分页错误"
    }
    ERR_MSG_SRC_PLATFORM_RELATIVE_WORKING_MIGRATION_TASK_EXISTS = {
        EN: u"relative working migration task exists error",
        ZH_CN: u"关联的迁移中的迁移任务存在"
    }
