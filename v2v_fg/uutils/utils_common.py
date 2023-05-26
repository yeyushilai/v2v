# -*- coding: utf-8 -*-

import base64
import datetime
import hashlib
import itertools
import random
import sys
import time
import uuid

reload(sys)
sys.setdefaultencoding('utf8')

from Crypto.Cipher import AES


# 检验是否全是中文字符
def is_all_chinese(strs):
    for _char in strs.decode("utf-8"):
        if not u'\u4e00' <= _char <= u'\u9fff':
            return False
    return True


# 检验是否含有中文字符
def is_contains_chinese(strs):
    for _char in strs.decode("utf-8"):
        if u'\u4e00' <= _char <= u'\u9fff':
            return True
    return False


# 生成uuid
def generate_uuid():
    return str(uuid.uuid4()).replace("-", "")


# 生成平台ID
def generate_platform_id():
    return "-".join(["plf", generate_uuid()[0:8]])


# 生成镜像ID
def generate_image_id():
    return "-".join(["img", generate_uuid()[0:8]])


# 生成迁移会话ID
def generate_session_id():
    return "-".join(["session", generate_uuid()[0:8]])


# 生成迁移任务ID
def generate_task_id():
    return "-".join(["task", generate_uuid()[0:8]])


def get_format_datetime(m_datetime, s_format="%Y-%m-%dT%H:%M:%SZ"):
    """返回datetime的格式字符"""
    return m_datetime.strftime(s_format)


# UTC时间
def now():
    utc_offset = time.timezone
    return datetime.datetime.fromtimestamp(time.time() + utc_offset)


# 本地时间
def now_local():
    return datetime.datetime.fromtimestamp(time.time())


# 手动分页
def chunked(it, n):
    marker = object()
    for group in (list(g) for g in itertools.izip_longest(
            *[iter(it)] * n, fillvalue=marker)):
        if group[-1] is marker:
            del group[group.index(marker):]
        yield group


def rand_str(num=10):
    return "".join(
        random.sample(
            "ABCDEFGHJKLMNPQRSTUVWXY23456789ABCDEFGHJKLMNPQRSTUVWXY23456789abcdefghjkmnpqrstuvwxy23456789abcdefghjkmnpqrstuvwxy23456789",
            num))  # noqa


def md5(s):
    if type(s) == str:
        s = s.encode("utf-8")
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def generate_id():
    s = "%s%s" % (int(time.time() * 10000), rand_str())
    return md5(s.encode('utf-8'))[8:24]


def aes_decode(text):
    enc = base64.urlsafe_b64decode(text)
    key = "MFwwDQYJKoZIhvcA"
    iv = key.decode('utf-8')
    key = key.decode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)
    dec = cipher.decrypt(enc)
    return str(dec[0:-ord(dec[-1])].decode('utf-8'))


def get_utf8_value(value):
    if sys.version < "3":
        if isinstance(value, unicode):
            return value.encode('utf-8')
        if not isinstance(value, str):
            value = str(value)
        return value
    else:
        return str(value)


def order_list_and_paginate(target_list, sort_key, offset,
                            limit, reverse=False):
    sort_ex = lambda x: x.get(sort_key)
    length = len(target_list)
    if length == 0:
        return target_list, length
    page = offset // limit
    target_list.sort(key=sort_ex, reverse=reverse)
    if limit <= 0:
        raise Exception("limit must gte 0")
    elif page > (length // limit):
        raise Exception("offset:[%s] out target_list paginate index[%s]" % (
            offset, length // limit))
    chunk_res = chunked(target_list, limit)
    chunk = next(itertools.islice(chunk_res, page, None))
    return chunk, length
