# coding:utf-8
import time
import hashlib
import logging
import requests
from ... import conf
from ... util.cache_util import cache_lock, cache
from ...user.models import User
from ..models import DingtalkLogin
from dingle.interface import get_api_client
import dingle.dingtalk.user as dingtalk_user_api

logger = logging.getLogger('dingtalk')
dingtalk_obj = None


class DingtalkApi(object):
    def __init__(self, **kwargs):
        token_key_prefix = kwargs.get('corp_id') or ''
        self.api_client = get_api_client(config_dict=kwargs,
                                         token_store=cache,
                                         token_key_prefix= token_key_prefix)

    def _api(self, method, path, **kw):
        url = '%s%s' % ('https://oapi.dingtalk.com', path)
        if method == 'GET':
            resp = requests.get(url, **kw)
        elif method == 'POST':
            resp = requests.post(url, **kw)
        else:
            resp = None
        logger.info({"action": "dingtalkApiCall",
                     "method": method, "path": path, "kw": kw,
                     "content": resp.content})
        return resp

    def get_access_token(self):
        return self.api_client.manager.get_access_token()

    def get_jsapi_ticket(self):
        return self.api_client.manager.get_jsapi_ticket()

    def getuserinfo(self, code):
        ret = dingtalk_user_api.getuserinfo(code)
        if ret['errcode'] == 0:
            return True, ret
        return False, ret

    def get_userdetail(self, userid):
        ret = dingtalk_user_api.get(userid)
        if ret['errcode'] == 0:
            return True, ret
        return False, ret

    def sign_js_api(self, noncestr, timestamp, jsapi_ticket, url):
        pairs = [('jsapi_ticket', jsapi_ticket), ('noncestr', noncestr),
                 ('timestamp', timestamp), ('url', url)]
        sign_str = '&'.join(["%s=%s" % (k, v) for (k, v) in pairs]).encode('utf-8')
        signature = hashlib.sha1(sign_str).hexdigest()
        return signature

    def get_dd_config(self, url, api_list=None):
        return self.api_client.manager.get_dd_config(url,
                                                     api_list=api_list)


if getattr(conf, 'DINGTALK', None):
    dingtalk_obj = DingtalkApi(**conf.DINGTALK)


def set_user_info_from_dingtalk(user, dingtalk_info, overwrite=False):
    '''
    Set user.info based on dingtalk_info.
    '''
    fields = ['name', 'email', 'mobile', 'jobnumber']
    user.info['dingtalk_id'] = dingtalk_info['userid']
    for field in fields:
        if user.info.get(field) != dingtalk_info.get(field):
            if user.info.get(field) and not overwrite:
                continue
            user.info[field] = dingtalk_info.get(field)


def get_or_create_dingtalk_user(dingtalk_id, dingtalk_info):
    '''
    Get or create an dingtalk login object,
    if conf.DINGTALK_AUTO_CREATE_USER is enabled, a new pauli
    user will be created when no user is matched current
    dingtalk login object.
    '''
    user = None
    with cache_lock('dingtalk_%s' % dingtalk_id):
        login = DingtalkLogin.objects(dingtalk_id=dingtalk_id).first()
        if login:
            user = User.objects(id=login.user_id).first()
            if user and not user.soft_del:
                set_user_info_from_dingtalk(user, dingtalk_info)
                user.save()
            login.info = dingtalk_info
            login.save()
        else:
            email = dingtalk_info.get('email') or dingtalk_info.get('orgEmail')
            if email:
                user = User.objects(info__email=email).first()
                if user and not user.soft_del:
                    set_user_info_from_dingtalk(user, dingtalk_info)
                    user.save()
                    login = DingtalkLogin(user_id=str(user.id),
                                          dingtalk_id=dingtalk_id,
                                          info=dingtalk_info)
                    login.save()
                elif getattr(conf, 'DINGTALK_AUTO_CREATE_USER', None):
                    user = User(name=dingtalk_info.get('name'))
                    set_user_info_from_dingtalk(user, dingtalk_info)
                    user.save()
                    login = DingtalkLogin(user_id=str(user.id),
                                          dingtalk_id=dingtalk_id,
                                          info=dingtalk_info)
                    login.save()
            if login:
                logger.info({"action": "createDingtalkUser",
                             "user_id": str(user.id),
                             "login_id": str(login.id),
                             "info": dingtalk_info})
        return user, login
