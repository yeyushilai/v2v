from log.logger import logger

import context
from constants import (
    API_DURATION,
    MC_KEY_MAP,
)
from resource_control.iaas.interface import (
    get_account_quota,
)


def get_access_count(user_id, api_type):
    """ get access count left during a period """
    ctx = context.instance()
    ret = ctx.mcm.get(MC_KEY_MAP[api_type], user_id)
    if ret is None:
        logger.debug('get api access count for user[%s:%s] failed'
                     % (user_id, api_type))
    return ret


def set_access_count(user_id, api_type, count, expires):
    """ set access count """
    ctx = context.instance()
    ret = ctx.mcm.set(MC_KEY_MAP[api_type], user_id, count, expires)
    if ret is None:
        logger.error("set api access count for user [%s:%s] failed"
                     % (user_id, api_type))
    return ret


def decr_access_count(user_id, api_type):
    """ decr access count left """
    ctx = context.instance()
    ret = ctx.mcm.decr(MC_KEY_MAP[api_type], user_id)
    if ret is None:
        logger.error("incr api access count for user [%s:%s] failed"
                     % (user_id, api_type))
    return ret


def check_api_access_count(user_id, api_type):
    """ check api access count """
    cnt = get_access_count(user_id, api_type)
    if cnt is None:
        # check user self api quota, do not shared with root user
        quotas = get_account_quota(user_id)
        if quotas is None:
            return None

        cnt = quotas[api_type]
        set_access_count(user_id, api_type, cnt,
                         quotas[API_DURATION[api_type]])

    if cnt <= 0:
        logger.warn("access too frequently [%d] for user [%s], ignore request"
                    % (cnt, user_id))
        return False

    decr_access_count(user_id, api_type)
    return True
