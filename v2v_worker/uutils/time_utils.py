# -*- coding: utf-8 -*-

import time
import datetime


def now():
    utc_offset = time.timezone
    return datetime.datetime.fromtimestamp(time.time() + utc_offset)


def now_local():
    """返回datetime格式的本地时间"""
    return datetime.datetime.fromtimestamp(time.time())


def now_local_format(s_format="%Y-%m-%dT%H:%M:%SZ"):
    """返回年、月、日、时、分、秒字符串格式的本地时间
    eg: '2021-10-20 20:22:33'
    """
    now_local_time = datetime.datetime.fromtimestamp(time.time())
    return now_local_time.strftime(s_format)


def get_format_datetime(m_datetime, s_format="%Y-%m-%dT%H:%M:%SZ"):
    """
    返回datetime的格式字符
    eg: '2021-10-20 20:22:33'
    """
    return m_datetime.strftime(s_format)


def now_local_timestamp():
    """本地时间的时间戳"""
    return int(time.time())


if __name__ == '__main__':
    print now()
    print now_local()
