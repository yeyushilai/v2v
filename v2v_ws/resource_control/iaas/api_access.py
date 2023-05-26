from api.error import Error
import api.error_code as ErrorCodes
import api.error_msg as ErrorMsg
from log.logger import logger

import context
from resource_control.iaas.interface import (
    check_user_lock,
)
from resource_control.iaas.access_limit import (
    check_api_access_count,
)
from constants import (
    USER_STATUS_ACTIVE,
    NO_PRIVILEGE,
    MGMT_PRIVILEGE,
    ROLE_GLOBAL_ADMIN,
    ROLE_ZONE_ADMIN,
    ROLE_CONSOLE_ADMIN,
)


def _check_access(user_info, req_zone=None):
    """ check access authority of user
       @return: None if succeeded and Error if failed
    """

    # check if user complete sign-up procedure
    verification_code = user_info['verification_code']
    if verification_code != "":
        logger.error("user [%s] not finish registration" % user_info)
        err = Error(ErrorCodes.PERMISSION_DENIED,
                    ErrorMsg.ERR_MSG_NOT_FINISH_REGISTRATION)
        return err

    # check if user is disable
    if user_info["status"] != USER_STATUS_ACTIVE:
        logger.error("user [%s] is not active" % user_info)
        err = Error(ErrorCodes.PERMISSION_DENIED,
                    ErrorMsg.ERR_MSG_USER_NOT_FOUND)
        return err

    # check if user has privilege
    if user_info["privilege"] == NO_PRIVILEGE:
        logger.error("user [%s] has no privilege to access" % user_info)
        err = Error(ErrorCodes.PERMISSION_DENIED,
                    ErrorMsg.ERR_MSG_ACCESS_DENIED_FOR_USER)
        return err

    # get zones that user can access
    zones = user_info["zone_info"]
    if zones is None:
        logger.error("access denied for user [%s]" % user_info)
        err = Error(ErrorCodes.PERMISSION_DENIED,
                    ErrorMsg.ERR_MSG_ACCESS_DENIED_FOR_USER)
        return err

    user_info['zones'] = zones.keys()

    # user can only access the zone that allowed
    if req_zone and req_zone != "global":
        if req_zone not in user_info['zones']:
            logger.error("user [%s] access denied for zone [%s]"
                         % (user_info, req_zone))
            err = Error(ErrorCodes.PERMISSION_DENIED,
                        ErrorMsg.ERR_MSG_ACCESS_DENIED_FOR_ZONE, req_zone)
            return err
        user_info['privilege'] = zones[req_zone]['privilege']
        user_info['role'] = zones[req_zone]['role']

    return None


def _check_user_lock(user_id, lock_type, action):
    # only read-only requests can be allowed
    err = None
    if not action:
        return True, err

    user_lock_status = check_user_lock(user_id, lock_type, api_action=action)
    if not user_lock_status or isinstance(user_lock_status, Error):
        err = Error(
            ErrorCodes.INTERNAL_ERROR,
            ErrorMsg.ERR_CODE_MSG_INTERNAL_ERROR,
        )
    if user_lock_status is "locked":
        err = Error(
            ErrorCodes.PERMISSION_DENIED,
            ErrorMsg.ERR_MSG_USER_IS_LOCKED,
        )

    if err:
        logger.warn("user [%s] is locked, action [%s] is not allowed via [%s]"
                    % (user_id, action, lock_type))
        return False, err

    return True, err


def _check_access_limit(user_id, api_type):
    """ check limit to prevent inappropriate api usage """
    if not check_api_access_count(user_id, api_type):
        err = Error(ErrorCodes.QUOTAS_EXCEEDED,
                    ErrorMsg.ERR_MSG_ACCESS_TOO_FREQUENTLY)
        logger.warn("access too frequently for user [%s], request is ignored"
                    % user_id)
        return False, err
    return True, None


def is_admin_user(user):
    """ check if user is admin user """
    if user["privilege"] >= MGMT_PRIVILEGE and user["role"] \
            in [ROLE_GLOBAL_ADMIN, ROLE_ZONE_ADMIN, ROLE_CONSOLE_ADMIN]:
        return True
    return False


def check_user_access(user_info, api_type, req_action,
                      is_pitrix_request, req_zone=None):
    # check if user can access
    error = _check_access(user_info, req_zone)
    if error:
        return None, error

    # check if user is locked
    if not is_pitrix_request:
        is_accessible, error = _check_user_lock(user_info['user_id'],
                                                api_type,
                                                req_action)
        if not is_accessible:
            return None, error

    # check access limit for normal users
    ctx = context.instance()
    if not is_admin_user(user_info) and ctx.check_access_limit:
        is_accessible, error = _check_access_limit(user_info['user_id'],
                                                   api_type)
        if not is_accessible:
            return None, error

    return user_info, None


def check_api_access_control(action, sender, channel):
    """ api access control """
    acl = APIAccessControl(sender, channel)
    if not action:
        logger.error("request without action field")
        error = Error(ErrorCodes.INVALID_REQUEST_FORMAT,
                      ErrorMsg.ERR_MSG_MISSING_PARAMETER, "action")
        return False, error
    if not acl.check_access(action):
        logger.error("check api access failed for [%s]" % sender)
        error = acl.get_error()
        return False, error

    return True, None


class APIAccessControl(object):
    """ each user role will have a corresponding api access list """

    def __init__(self, sender, channel):
        """
        @param sender - the info of the sender of the request
        """
        self.sender = sender
        self.role = sender['role']
        self.channel = channel
        self.API_ACL = dict()
        # error message
        self.error = Error(ErrorCodes.PERMISSION_DENIED)

        from handlers.api_acl.common import get_api_acl_map

        self.API_ACL.update(get_api_acl_map())

    def get_error(self):
        """ return the information describing the error occurred
            in Request Builder.
        """
        return self.error

    def set_error(self, code, msg=None, args=None):
        """ set error """
        self.error = Error(code, msg, args)

    def check_access(self, action):
        """ check api access """
        if action is None:
            logger.debug("api_acl 0")
            logger.error("action can not be None")
            self.set_error(ErrorCodes.INVALID_REQUEST_FORMAT,
                           ErrorMsg.ERR_MSG_MISSING_PARAMETER, "action")
            return False
        from utils.misc import (
            is_str
        )
        if not is_str(action):
            logger.debug("api_acl 1")
            logger.error("illegal action [%s] of sender [%s]" % (
                action, self.sender))
            self.set_error(ErrorMsg.ERR_MSG_PARAMETER_SHOULD_BE_STR, "action")
            return None

        if action not in self.API_ACL:
            logger.error("check_access action: %s" % action)
            logger.error("can not handle this action [%s] for sender [%s]" % (
                action, self.sender))
            self.set_error(ErrorCodes.PERMISSION_DENIED,
                           ErrorMsg.ERR_MSG_CAN_NOT_HANDLE_REQUEST)
            return False
        from api.constants import CHANNEL_INTERNAL
        if self.channel == CHANNEL_INTERNAL:
            logger.debug("api_acl 3")
            return True

        if self.channel not in self.API_ACL[action]:
            logger.debug("api_acl 4")
            logger.error("can not handle action [%s] through channel [%s] for sender [%s]" % (
                action, self.channel, self.sender))
            self.set_error(ErrorCodes.PERMISSION_DENIED,
                           ErrorMsg.ERR_MSG_CAN_NOT_HANDLE_REQUEST)
            return False
        if self.role not in self.API_ACL[action][self.channel]:
            logger.debug("api_acl 5")
            logger.error("can not handle action [%s] for role [%s], sender [%s]" % (
                action, self.role, self.sender))
            self.set_error(ErrorCodes.PERMISSION_DENIED,
                           ErrorMsg.ERR_MSG_CAN_NOT_HANDLE_REQUEST)
            return False

        return True
