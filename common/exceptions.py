# -*- coding: utf-8 -*-


class PauliException(Exception):
    def __init__(self, *subs):
        # Add a default empty string for subs
        if not subs:
            subs = [""]
        Exception.__init__(self, *subs)
