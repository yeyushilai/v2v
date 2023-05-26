"""
Created on 2012-7-9

@author: yunify
"""
import sys
import base64
import hmac
from urllib import quote, unquote, quote_plus
from log.logger import logger
import hashlib
from hashlib import sha256 as sha256
from urlparse import urlparse, parse_qs
from comm.base_client import ReqLetter
from utils.json import json_dump, json_load
from random import choice

import context
from common.misc import get_iam_signature_servers
from constants import (
    TIMEOUT_IAM_SIGNATURE_SERVER_LONG,
    IAM_SIGNATURE_SERVER_PROXY_PORT,
)


def process_canonical_query_string(query):
    query = dict(query)
    params = []
    for param in query:
        if param in [u'signature']:
            continue
        params.append(param)
    params.sort()

    canonical_query_param = []
    for key in params:
        value = query[key]
        k = quote(key)
        if type(value) is list:
            value.sort()
            for v in value:
                if isinstance(v, unicode):
                    kv = k + "=" + quote(v.encode('utf8'))
                else:
                    kv = k + "=" + quote(str(v))
                canonical_query_param.append(kv)
        elif isinstance(value, unicode):
            kv = k + "=" + quote(value.encode('utf8'))
            canonical_query_param.append(kv)
        else:
            kv = k + "=" + quote(str(value))
            canonical_query_param.append(kv)

    return '&'.join(canonical_query_param)


def process_canonical_uri(path):
    pattens = unquote(path).split('/')
    uri = []
    for v in pattens:
        uri.append(quote(v))
    url_path = "/".join(uri)

    if url_path[-1] != '/':
        url_path = url_path + "/"

    return url_path


def hex_encode_md5_hash(data):
    if not data:
        data = ""
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()


def check_signature_via_iam(access_key_id, signature, request):
    """ main function """

    # parser options
    req_headers = {}
    req_signed_headers = []
    for k, v in request.headers.iteritems():
        req_headers.update({k: v})
    parsed_url = urlparse(request.url)
    req_path = process_canonical_uri(parsed_url[2])
    req_method = request.method.upper()
    req_body = request.body
    req_query_string = process_canonical_query_string(request.query)

    params = {
        "action": "ValidateRequestSignature",
        "req_method": req_method,
        "req_headers": req_headers,
        "req_signed_headers": req_signed_headers,
        "req_path": req_path,
        "req_query_string": req_query_string,
        "req_body": req_body,
        "req_signature": signature,
        "req_access_key_id": access_key_id,
    }
    req = {
        "type": "internal",
        "params": params
    }

    signature_servers = get_iam_signature_servers()
    if not signature_servers:
        logger.critical("get signature_servers failed")
        return None

    host = choice(signature_servers)
    port = IAM_SIGNATURE_SERVER_PROXY_PORT
    # send request
    logger.info("sending request [%s] to iam singature server [%s:%s]"
                % (req, host, port))
    letter = ReqLetter("tcp://%s:%s" % (host, port), json_dump(req))

    ctx = context.instance()
    rep = json_load(ctx.client.send(letter, 0,
                                    TIMEOUT_IAM_SIGNATURE_SERVER_LONG))
    if rep is None or rep['ret_code'] != 0:
        logger.error("receive reply failed on iam signature server [%s:%s], "
                     " rep[%s]" % (host, port, rep))
        return None
    return rep


class HmacKeys(object):
    """Key based Auth handler helper."""

    def __init__(self, host, access_key_id, secret_access_key):
        self.host = host
        self.access_key_id = access_key_id
        if sys.version_info[0] >= 3:
            self.secret_access_key = bytes(secret_access_key, "utf-8")
        else:
            self.secret_access_key = bytes(secret_access_key).encode('utf-8')

    def sign_string(self, string_to_sign):
        logger.debug(string_to_sign)
        print string_to_sign
        if self._hmac_256:
            h = self._hmac_256.copy()
        else:
            h = self._hmac.copy()
        h.update(string_to_sign.encode("utf-8"))
        signature = base64.b64encode(h.digest()).strip()

        return quote_plus(signature)


class SignatureAuthHandler(HmacKeys):
    """ Provides API Signature Authentication. """

    SignatureVersion = 1

    @staticmethod
    def process_canonical_request(req):
        """ build string to signature """
        hex_encode = hex_encode_md5_hash(req.body)
        parsed_url = urlparse(req.url)
        canonical_uri = process_canonical_uri(parsed_url[2])
        canonical_query_string = process_canonical_query_string(
            parse_qs(parsed_url[4]))
        return "%s\n%s\n%s\n%s" % (req.method.upper(), canonical_uri,
                                   canonical_query_string, hex_encode)

    def _calc_signature(self, req):
        """ calc signature for request """

        self._hmac_256 = hmac.new(self.secret_access_key,
                                  digestmod=sha256)
        string_to_sign = SignatureAuthHandler.process_canonical_request(req)
        signature = self.sign_string(string_to_sign)
        logger.debug('signature [%s]' % signature)
        return signature

    def check_auth(self, req, ori_signature, **kwargs):
        """ check authorize information for request """
        signature = self._calc_signature(req)
        if ori_signature != signature.decode("utf-8"):
            logger.error('signature not match [%s] [%s]'
                         % (ori_signature, signature))
            return False
        return True
