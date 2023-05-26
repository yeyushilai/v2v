# -*- coding: utf-8 -*-

import threading

from log.logger import logger

from vm import VMSession
from constants.common import WorkerAction


class MigrateHandler(object):
    # 先预留
    pass


class ImmediatelyMigrateHandler(MigrateHandler):
    action = WorkerAction.IMMEDIATELY_MIGRATE.value
    """立刻开始迁移handler类"""

    def __init__(self, params, *args, **kwargs):
        super(ImmediatelyMigrateHandler, self).__init__(*args, **kwargs)
        self.vm_session_info = params

    def start(self):
        """发起迁移"""
        session_id = self.vm_session_info["session_id"]
        user_id = self.vm_session_info["user_id"]

        logger.info("=====================================")
        logger.info("vm start migrate, session id: {session_id}, "
                    "action: {action}, user id: {user_id}"
                    .format(session_id=session_id,
                            action=self.action,
                            user_id=user_id))
        vm_session = VMSession(session_id)
        vm_session.info = self.vm_session_info
        vm_session.migrate()


class TimeMigrateHandler(MigrateHandler):
    action = WorkerAction.TIME_MIGRATE.value
    """定时开始迁移handler类"""

    def __init__(self, params, *args, **kwargs):
        super(TimeMigrateHandler, self).__init__(*args, **kwargs)
        self.vm_session_info = params

    def start(self):
        pass


class ConcurrencyImmediatelyMigrateHandler(MigrateHandler, 
                                           threading.Thread):
    """并发立刻开始迁移handler类"""
    action = WorkerAction.IMMEDIATELY_MIGRATE.value

    def __init__(self, params, *args, **kwargs):
        super(ConcurrencyImmediatelyMigrateHandler, self).__init__(*args, **kwargs)
        self.vm_session_info = params

    def run(self):
        """发起迁移"""
        session_id = self.vm_session_info["session_id"]
        user_id = self.vm_session_info["user_id"]

        logger.info("=====================================")
        logger.info("vm start migrate, user id: {user_id}, session id: "
                    "{session_id}, action: {action} "
                    .format(session_id=session_id,
                            action=self.action,
                            user_id=user_id))
        vm_session = VMSession(session_id)
        vm_session.info = self.vm_session_info
        vm_session.migrate()


class ConcurrencyTimeMigrateHandler(MigrateHandler,
                                    threading.Thread):
    """并发定时开始迁移handler类"""
    action = WorkerAction.TIME_MIGRATE.value

    def __init__(self, params, *args, **kwargs):
        super(ConcurrencyTimeMigrateHandler, self).__init__(*args, **kwargs)
        self.vm_session_info = params

    def run(self):
        """发起迁移"""
        pass


concurrency_action_handler_mapper = {
    WorkerAction.IMMEDIATELY_MIGRATE.value: ConcurrencyImmediatelyMigrateHandler,
    WorkerAction.TIME_MIGRATE.value: ConcurrencyTimeMigrateHandler
}

action_handler_mapper = {
    WorkerAction.IMMEDIATELY_MIGRATE.value: ImmediatelyMigrateHandler,
    WorkerAction.TIME_MIGRATE.value: TimeMigrateHandler
}
