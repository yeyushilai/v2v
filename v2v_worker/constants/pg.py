# -*- coding: utf-8 -*-

from enum import Enum

MIN_CONNECT = 0
MAX_CONNECT = 1000

DSTINSTANCECLASSPREFIX = "instance_class_"
DSTVOLUMETYPEPREFIX = "volume_type_"


class JobTableStatus(Enum):
    DONE_WITH_FAILURE = "done with failure"
    FAILED = "failed"
    WORKING = "working"
    SUCCESSFUL = "successful"
    PENDING = "pending"

    @classmethod
    def list_status(cls):
        return [
            cls.PENDING.value,
            cls.DONE_WITH_FAILURE.value,
            cls.FAILED.value,
            cls.WORKING.value,
            cls.SUCCESSFUL.value
        ]
