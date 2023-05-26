# -*- coding: utf-8 -*-

from fg import context

ctx = context.instance()


def discover_v2v_worker():
    return ctx.zk.get_children("/v2v_worker")
