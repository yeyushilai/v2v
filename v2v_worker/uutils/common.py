# -*- coding: utf-8 -*-

"""功能：通用的工具定义"""

import time
import os
import datetime

import tempfile
import hashlib
import subprocess
import base64
from Crypto.Cipher import AES


def get_file_size(file_path, unit="mb"):
    if unit == "mb":
        return round(os.path.getsize(file_path) / float(1024 * 1024), 2)
    else:
        # TODO:待开发
        raise


def find_file(file_path, file_name_list, fuzzy_search=False):

    compare_file_prefix_list = list()
    compare_file_format_list = list()
    if fuzzy_search:
        for file_name in file_name_list:
            compare_file_prefix, compare_file_format = file_name.split(".")
            compare_file_prefix_list.append(compare_file_prefix)
            compare_file_format_list.append(compare_file_format)

    for dir, folders, files in os.walk(file_path):
        for s_file in files:
            if "." not in s_file:
                continue
            if fuzzy_search:
                file_prefix, file_format = s_file.split(".")
                if (file_prefix in compare_file_prefix_list) and (
                        file_format in compare_file_format_list):
                    return True
            else:
                if s_file in file_name_list:
                    return True
    return False


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


def dict_to_obj(dict_obj):
    if not isinstance(dict_obj, dict):
        return dict_obj
    d = Dict()
    for k, v in dict_obj.items():
        d[k] = dict_to_obj(v)
    return d


def aes_decode(text):
    enc = base64.urlsafe_b64decode(text)
    key = "MFwwDQYJKoZIhvcA"
    iv = key.decode('utf-8')
    key = key.decode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)
    dec = cipher.decrypt(enc)
    return str(dec[0:-ord(dec[-1])].decode('utf-8'))


def normal_exec(argv, timeout=60):
    start_time = datetime.datetime.now()
    pipe = subprocess.Popen(argv,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)

    # pipe.poll()为None 说明没有执行完毕
    while pipe.poll() is None:
        end_time = datetime.datetime.now()
        total_seconds = (end_time - start_time).total_seconds()
        if total_seconds > timeout:
            pipe.terminate()
            raise Exception(
                "exec cmd timeout, cmd: %s, timeout: %s" % (argv, timeout))
        time.sleep(0.1)

    stdout, stderr = pipe.communicate()
    return pipe.returncode, stdout.strip(), stderr.strip()


def bash_exec(cmd, timeout=60, dir='/tmp', bin='/bin/bash -x '):
    tmp_file_path = tempfile.mktemp(suffix='.sh', prefix='_v2v_', dir=dir)
    with open(tmp_file_path, 'w') as f:
        f.write(cmd)
    cmd = "{bin} {tmp_file_path} ".format(bin=bin, tmp_file_path=tmp_file_path)
    # eg: /bin/bash -x /tmp/v2v_bash/_v2v_xMn1i_.sh
    return normal_exec(cmd, timeout)


def singleton(cls):
    _instance = {}
    global istc

    def _singleton(*args, **kargs):
        if cls not in _instance:
            istc = cls(*args, **kargs)
            _instance[cls] = istc
        return _instance[cls]

    return _singleton


def read_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    return content


def write_file(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)


def sha256_tool(content):
    sha = hashlib.sha256()
    sha.update(content)
    ret = sha.hexdigest()
    return ret
