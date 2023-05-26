# -*- coding: utf-8 -*-

from health_acl import API_ACL_V2V_HEALTH
from iaas_acl import API_ACL_V2V_IAAS
from migration_task_acl import API_ACL_V2V_MIGRATION_TASK
from migration_vm_acl import API_ACL_V2V_MIGRATION_VM
from nas_acl import API_ACL_V2V_NAS
from src_platform_acl import API_ACL_V2V_SRC_PLATFORM


def get_api_acl_map():

    API_ACL_V2V = dict()
    API_ACL_V2V.update(API_ACL_V2V_HEALTH)
    API_ACL_V2V.update(API_ACL_V2V_IAAS)
    API_ACL_V2V.update(API_ACL_V2V_MIGRATION_TASK)
    API_ACL_V2V.update(API_ACL_V2V_MIGRATION_VM)
    API_ACL_V2V.update(API_ACL_V2V_NAS)
    API_ACL_V2V.update(API_ACL_V2V_SRC_PLATFORM)
    
    return API_ACL_V2V
