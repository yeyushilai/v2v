# -*- coding: utf-8 -*-

"""功能：定义通用的基类"""


class Base(object):

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self._user_id = None

    @property
    def user_id(self):
        if self._user_id is None:
            if hasattr(self, "config"):
                self._user_id = self.config["user_id"]
            if hasattr(self, "info"):
                self._user_id = self.info["user_id"]
        return self._user_id
