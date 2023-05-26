from api.error import Error
import api.error_code as ErrorCodes
import api.error_msg as ErrorMsg
from log.logger import logger

from resource_control.iaas.interface import (
    get_user,
)
import context as context
from resource_control.iaas.interface import get_access_key
from constants import ACCESS_KEY_STATUS_ACTIVE
from common.auth import (
    SignatureAuthHandler,
    check_signature_via_iam,
)
from pprint import pformat


def check_signature(apikey, required_scopes=None, request=None):
    """
    check signature
    :param apikey: string with "access_key" + "ori_signature"
    :param required_scopes:
    :param request: request parameter
    :return: token_info
    """
    ctx = context.instance()
    logger.debug("check signature start, api key: %s, request: %s"
                 % (apikey, pformat(request.__dict__)))

    signature = apikey.encode("utf-8")
    access_key_id = request.query.get("access_key_id")
    no_check = request.query.get("no_check")
    if no_check:
        access_key = get_access_key(access_key_id)
        if access_key is None:
            logger.error("get access_key for [%s] failed" % access_key_id)
            return None
        elif access_key['status'] != ACCESS_KEY_STATUS_ACTIVE:
            logger.error("access_key[%s] is not active [%s]"
                         % (apikey, access_key['status']))
            return None
        # check authorize information for request
        user_id = str(access_key["owner"])
        user_info = get_user(user_id)
        if not user_info:
            logger.error("get user for [%s] failed" % user_id)
            err = Error(ErrorCodes.PERMISSION_DENIED,
                        ErrorMsg.ERR_MSG_USER_NOT_FOUND)
            return None, err
        logger.debug("check signature end, api key: %s, request: %s"
                     % (apikey, pformat(request.__dict__)))
        return {'sub': user_info, 'uid': user_id, 'access_key': access_key}

    if ctx.verify_signature_via_iam:
        user_info = check_signature_via_iam(access_key_id, signature, request)
        if user_info and user_info.get("zone_info"):
            user_id = user_info.get('user_id')
            access_key = {"controller": "self"}
        else:
            logger.error("check signature via iam failed, ak[%s],"
                         " signature[%s] request[%s]"
                         % (access_key_id, signature, request))
            err = Error(ErrorCodes.AUTH_FAILURE,
                        ErrorMsg.ERR_MSG_SIGNATURE_NOT_MACTCHED)
            return None, err
    else:
        access_key = get_access_key(access_key_id)
        if access_key is None:
            logger.error("get access_key for [%s] failed" % access_key_id)
            return None
        elif access_key['status'] != ACCESS_KEY_STATUS_ACTIVE:
            logger.error("access_key[%s] is not active [%s]"
                         % (apikey, access_key['status']))
            return None

        secret_access_key = access_key['secret_access_key']
        # check authorize information for request
        auth_handler = SignatureAuthHandler("", access_key_id, secret_access_key)
        if not auth_handler.check_auth(request, signature):
            logger.error("check auth for [%s] failed" % request)
            return None

        user_id = str(access_key["owner"])
        user_info = get_user(user_id)
        if not user_info:
            logger.error("get user for [%s] failed" % user_id)
            err = Error(ErrorCodes.PERMISSION_DENIED,
                        ErrorMsg.ERR_MSG_USER_NOT_FOUND)
            return None, err
        logger.debug("check signature end, api key: %s, request: %s"
                     % (apikey, pformat(request.__dict__)))

    return {'sub': user_info, 'uid': user_id, 'access_key': access_key}
