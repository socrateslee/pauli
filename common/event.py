# -*- coding: utf-8 -*-
import logging
import time
import json
import blinker

logger = logging.getLogger(__name__)

default = blinker.signal("pauli-default")


@default.connect
def event_log(*sub, **message):
    logger.info(json.dumps({
        "sender": sub,
        "message": message,
        "timestamp": int(time.time())
    }))
