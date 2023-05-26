# -*- coding: utf-8 -*-

# controllers
CONTROLLER_SELF = "self"
CONTROLLER_PITRIX = "pitrix"
SUPPORTED_CONTROLLERS = [CONTROLLER_SELF, CONTROLLER_PITRIX]
API_SECURE_PORTS = 8882

PITRIX_CONF_HOME = "/pitrix/conf"
# ---------------------------------------------
#       The constants for access key status
# ---------------------------------------------
ACCESS_KEY_STATUS_ACTIVE = "active"
ACCESS_KEY_STATUS_INACTIVE = "inactive"
ACCESS_KEY_STATUS_DISABLED = "disabled"
ACCESS_KEY_NAME_FOR_MGMT = "pitrix access key for mgmt"

# ---------------------------------------------
#       The constants for api timeout
# ---------------------------------------------
# time interval when client's request expired in seconds
REQ_EXPIRED_INTERVAL = 60

# time out when sending request to front_gate
TIMEOUT_FRONT_GATE = 30
TIMEOUT_FRONT_GATE_FAST = 1
TIMEOUT_FRONT_GATE_FAST_RATE = 80

# time out when sending request to billing server
TIMEOUT_BILLING_SERVER = 60

# time out when sending request to notifier server
TIMEOUT_NOTIFIER_SERVER = 5

# time out when sending request to account server
TIMEOUT_ACCOUNT_SERVER = 5
TIMEOUT_ACCOUNT_SERVER_LONG = 10
TIMEOUT_IAM_SIGNATURE_SERVER_LONG = 10

# long handle time
LONG_HANDLE_TIME = 20

# ---------------------------------------------
#       The constants for users
# ---------------------------------------------
# management user id
MGMT_USER_ID = "yunify"  # management user with the highest privilege
# system user id
SYSTEM_USER_ID = "system"  # providing public resources like image template and vxnet-0
# system console id
SYSTEM_CONSOLE_ID = "system"  # system console id

# user privilege
NO_PRIVILEGE = 0  # access denied for all pitrix service
NORMAL_PRIVILEGE = 1  # normal user
MGMT_PRIVILEGE = 5  # mgmt user, can migrate instance, but not allowed to modify other users' resources
MGMT_PRIVILEGE_7 = 7  # mgmt user and can describe billing data
MGMT_PRIVILEGE_8 = 8  # mgmt user and can get access secrect key
SUPER_PRIVILEGE = 10  # highest privilege, can do any thing, only "yunify" user has this privilege.

# all normal partner privilege is 10
APP_REVIEW_PRIVILEGE = 2  # for high level partner, can review apps

# roles
ROLE_NORMAL_USER = "user"  # normal user
ROLE_PARTNER = "partner"  # partner
ROLE_AGENT = "agent"  # agent
ROLE_ZONE_ADMIN = "zone_admin"  # zone admin, can manager resources in zone
ROLE_CONSOLE_ADMIN = "console_admin"  # console admin, can manage all resources belong to this console
ROLE_GLOBAL_ADMIN = "global_admin"  # global admin, can manager all resources
ROLE_TICKET_MGR = "ticket_mgr"  # ticket manager, reply user tickets.

# ---------------------------------------------
#       Constants for Memcached key prefix
# ---------------------------------------------
MC_KEY_PREFIX_ROOT = "Pitrix.V2v"

# zone cached in ws server
MC_KEY_PREFIX_ZONE = "%s.Zone" % MC_KEY_PREFIX_ROOT
MC_KEY_PREFIX_ZONES = "%s.Zone" % MC_KEY_PREFIX_ROOT

# account
MC_KEY_PREFIX_ACCOUNT = "%s.ZoneAccount" % MC_KEY_PREFIX_ZONE
MC_KEY_PREFIX_ACCOUNT_USER_SET = "%s.UserSet" % MC_KEY_PREFIX_ROOT

# account cached in ws server.
MC_KEY_PREFIX_ACCOUNT_USER_INFO = "%s.UserInfo" % MC_KEY_PREFIX_ACCOUNT
MC_KEY_PREFIX_ACCOUNT_ACCESS_KEY = "%s.AccessKey" % MC_KEY_PREFIX_ACCOUNT
MC_KEY_PREFIX_ACCOUNT_USER_LOCK = "%s.UserLock" % MC_KEY_PREFIX_ACCOUNT
MC_KEY_PREFIX_ACCOUNT_QUOTA = "%s.Quota" % MC_KEY_PREFIX_ACCOUNT
MC_KEY_PREFIX_CERTIFICATES = "%s.Certificates" % MC_KEY_PREFIX_ROOT
MC_KEY_PREFIX_ACCOUNT_USER_ZONE = "%s.UserZone" % MC_KEY_PREFIX_ACCOUNT
MC_DEFAULT_CACHE_TIME = 3600 * 24

# ---------------------------------------------
#       languages
# ---------------------------------------------
EN = "en"
ZH_CN = "zh-cn"
DEFAULT_LANG = EN
SUPPORTED_LANGS = [EN, ZH_CN]

# ---------------------------------------------
#       zone status
# ---------------------------------------------
ZONE_STATUS_ACTIVE = "active"
ZONE_STATUS_FAULTY = "faulty"
ZONE_STATUS_DEFUNCT = "defunct"

# ---------------------------------------------
#       user status
# ---------------------------------------------
USER_STATUS_ACTIVE = "active"
USER_STATUS_DISABLED = "disabled"
USER_STATUS_DELETED = "deleted"
USER_STATUS_PENDING = "pending"

# ---------------------------------------------
#       Action
# ---------------------------------------------
# Account
ACTION_DESCRIBE_USERS = "DescribeUsers"
ACTION_DESCRIBE_USER_LOCKS = "DescribeUserLocks"
ACTION_DESCRIBE_ACCOUNT_QUOTAS = "DescribeAccountQuotas"
ACTION_DESCRIBE_ACCESS_KEYS = "DescribeAccessKeys"
ACTION_DESCRIBE_DEFAULT_ZONES = "DescribeDefaultZones"
ACTION_DESCRIBE_ZONES = "DescribeZones"

ACTION_GET_PRIVATE_KEY = "GetPrivateKey"
ACTION_GET_SECRET_ACCESS_KEY = "GetSecretAccessKey"
ACTION_GET_VPN_CERTS = "GetVPNCerts"

# ---------------------------------------------
#       The constants for action related
# ---------------------------------------------
# actions allowed where user is locked other than Describe* and Get*
LOCK_ALLOWED_ACTIONS = []

# Describe* and Get* actions that disallowed when user is locked
LOCK_DISALLOWED_ACTIONS = [
    ACTION_GET_PRIVATE_KEY,
    ACTION_GET_SECRET_ACCESS_KEY,
    ACTION_GET_VPN_CERTS
]

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

# ---------------------------------------------
#       The constants for api types
# ---------------------------------------------
API_TYPE_V2V = "v2v_api"
SUPPORTED_API_TYPES = [
    API_TYPE_V2V,
]
API_DURATION = {API_TYPE_V2V: 'v2v_api_duration'}

# limitation on api access count during a period of time
MC_KEY_PREFIX_V2V_API_ACCESS_COUNT = "%s.V2vApiAccessCnt" % MC_KEY_PREFIX_ROOT

MC_KEY_MAP = {API_TYPE_V2V: MC_KEY_PREFIX_V2V_API_ACCESS_COUNT}


SERVER_TYPE_IAM_SIGNATURE = "signature_server"
IAM_SIGNATURE_SERVER_PROXY_PORT = 9389

ZONE_SERVER_CACHE_TIME = 600
