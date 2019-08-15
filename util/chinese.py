# -*- coding: utf-8 -*-
'''
Utility for chinese
'''

NUM_MAP = {
    "零": "0",
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
    "十": "10"
}


def chinese_num_replace(s):
    if not s:
        return s
    return ''.join([NUM_MAP.get(i, i) for i in s])
