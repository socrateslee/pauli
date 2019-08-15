# coding:utf-8
'''
Decorator for login and permission.
'''
import functools
import flask
from ...util import api_base
from ...auth.ops import common
from . import user_perm


def perm_required(perms=None):
    '''
    用于检查用户登录及基本的权限。
    '''
    if perms and not isinstance(perms, (tuple, list)):
        perms = [perms]
    def entangle(func):
        @functools.wraps(func)
        def wrapper(*sub, **kw):
            if not common.is_logined(flask.request, flask.session):
                return api_base.send_json_result("USER_NOT_LOGIN")
            if perms:
                for perm in perms:
                    if not user_perm.has_perm(flask.session['user_id'],
                                              perm):
                        return api_base.send_json_result("FORBIDDEN",
                                                         msg="缺少权限%s" % str(perm))
            ret = func(*sub, **kw)
            return ret
        return wrapper
    return entangle
