# -*- coding: utf-8 -*-

import time

from log.logger import logger
from api.common import is_admin_user, is_normal_user_only, is_api_request
from api.constants import JOB_RESOURCES, JOB_EXTRAS, JOB_STATUS_DONE_FAIL, \
                          JOB_STATUS_FAIL, JOB_STATUS_SUCC, \
                          DEFAULT_JOB_WAIT_TIME
from api.error_msg import EN
from api.error import Error
from utils.misc import explode_array, fuzzy_attribute
from utils.json import json_load, json_dump

from fg import context
from fg.constants import TB_JOB


def sift_through_job_resources(job, directive):
    job["resources"] = {}
    resource_ids = []

    for resource in JOB_RESOURCES:
        if resource in directive:
            directive_resource_ids = directive[resource]
            job["resources"][resource] = directive_resource_ids

            if isinstance(directive_resource_ids, (list, tuple)):
                resource_ids.extend(directive_resource_ids)

            elif isinstance(directive_resource_ids, basestring):
                resource_ids.append(directive_resource_ids)
    job["resource_ids"] = " ".join(resource_ids)


def decorate_job(job, sender=None):
    """ decorate job """
    if "directive" not in job:
        return job
    directive = json_load(job["directive"])
    if directive is None:
        logger.error("load json [job directive] [%s] failed"
                     % job["directive"])
        return job

    # fuzzy sensitive info
    fuzzy_attribute(directive, "login_passwd")
    job["directive"] = json_dump(directive)

    # job related resources
    sift_through_job_resources(job, directive)
            
    # translate error codes
    if 'error_codes' in job and job['error_codes']:
        error_info = []
        lang = sender.get("lang", EN) if sender is not None else EN
        error_codes = explode_array(job['error_codes'])
        for code in error_codes:
            code = int(code)
            error = Error(code)
            error_info.append({'err_code': error.get_code(),
                               'err_msg': error.get_message(lang)})
        job['err_codes'] = error_info
        del job['error_codes']

    # job related extra parameters
    job["extras"] = {}
    for extra in JOB_EXTRAS:
        if extra in directive:
            job["extras"][extra] = directive[extra]

    # normal user not allowed to obtain job "directive"
    if sender is not None and not is_admin_user(sender) and "directive" in job:
        del job["directive"]
        
    # delete some parameters for normal user's API requests
    if sender is not None and is_normal_user_only(sender) \
            and is_api_request(sender):
        for param in ["resources", "extras"]:
            if param in job:
                del job[param]
    return job


def wait_job_done(job_id, time_out=DEFAULT_JOB_WAIT_TIME, interval=2):
    """ wait for job done """
    ctx = context.instance()
    cnt = 0
    while cnt < time_out/interval:
        job = ctx.zone_pg.get(TB_JOB, job_id)
        if job is None:
            logger.error("get job [%s] failed" % job_id)
            return None
        status = job['status']
        if status in [JOB_STATUS_DONE_FAIL, JOB_STATUS_FAIL, JOB_STATUS_SUCC]:
            return status
        time.sleep(interval)
        cnt += 1
    
    logger.error("wait for job [%s] done timeout after waiting for "
                 "[%s] seconds" % (job_id, time_out))
    return None
