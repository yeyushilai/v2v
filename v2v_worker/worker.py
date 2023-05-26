# -*- coding: utf-8 -*-


class Worker(object):
    """V2V Worker类"""

    def __init__(self, concurrency_migrate=None):
        self.concurrency_migrate = concurrency_migrate
        self.thread_worker_mapper = dict()

    def start(self, action, params):
        """执行worker的业务处理"""
        if self.concurrency_migrate:
            from handler import concurrency_action_handler_mapper
            handler_quote = concurrency_action_handler_mapper[action]
            handler = handler_quote(params)
            handler.setDaemon(True)
            handler.start()

            # 纳入监管
            worker = dict(action=action, params=params)
            self.thread_worker_mapper[handler] = worker
        else:
            from handler import action_handler_mapper
            handler_quote = action_handler_mapper[action]
            handler = handler_quote(params)
            handler.start()
    
    @property
    def workers(self):
        return [worker for worker in self.thread_worker_mapper.values()]

    @property
    def threads(self):
        return [thread for thread in self.thread_worker_mapper.keys()]

    @property
    def alive_threads(self):
        return [thread for thread in self.threads if thread.is_alive()]

    @property
    def dead_threads(self):
        return [thread for thread in self.threads if not thread.is_alive()]

    @property
    def threads_num(self):
        return len(self.threads)

    @property
    def alive_threads_num(self):
        return len(self.alive_threads)

    @property
    def dead_threads_num(self):
        return len(self.dead_threads)
