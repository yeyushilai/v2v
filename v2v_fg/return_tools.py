# -*- coding: utf-8 -*-

from utils.json import json_dump
from api import error_msg


def return_error(req, error, dump=True, **kwargs):
    response = {}
    for k in kwargs:
        response[k] = kwargs[k]

    lang = error_msg.EN if (req is None or "sender" not in req) \
        else req["sender"].get("lang", error_msg.EN)
    response["ret_code"] = error.code
    response["message"] = error.get_message(lang)

    if dump:
        return json_dump(response)
    else:
        return response


def return_success(req, rep, dump=True, **kwargs):
    assert "action" in req

    rep = rep or {}
    rep["ret_code"] = 0
    rep["action"] = req["action"] + "Response"

    for k in kwargs:
        rep[k] = kwargs[k]

    if dump:
        return json_dump(rep)
    else:
        return rep
