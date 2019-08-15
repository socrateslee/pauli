# coding: utf-8
import time
import json
import uuid
import flask
from ... import conf, pauli_root
from ...util import api_base
from ..ops import common
from ..ops import  pass_auth
from ...user.ops import user_base
from ...perm.ops import user_perm
from ...perm.ops.decr import perm_required


@pauli_root.route('/auth/api/dump', methods=['GET'])
def dump():
    result = {'sid': flask.session.sid,
              'is_logined': common.is_logined(flask.request, flask.session)}
    return api_base.send_json_result("SUCC", result=result)


@pauli_root.route('/auth/api/logined', methods=['GET'])
def logined():
    logined = common.is_logined(flask.request, flask.session)
    result = {'logined': logined}
    if logined:
        result.update(user_base.to_dict(flask.request.user))
    return api_base.send_json_result("SUCC", result=result)


@pauli_root.route('/auth/api/logout', methods=['GET'])
def logout():
    common.logout(flask.request, flask.session)
    return api_base.send_json_result("SUCC")


@pauli_root.route('/auth/api/record', methods=['GET'])
@perm_required("pauli:user:audit")
def api_login_record():
    '''
    获取用户的登录记录
    '''
    user_id = flask.request.args.get('user_id')
    cursor_id = flask.request.args.get('cursor_id') or ''
    limit = int(flask.request.args.get('limit') or 10)
    if not user_id:
        return api_base.send_json_result("PARAM")
    status, obj = common.get_user_login_record(user_id,
                                               cursor_id=cursor_id,
                                               limit=limit)
    if status:
        return api_base.send_json_result("SUCC", result={'logs': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/auth/api/pass/login', methods=['PUT'])
def pass_login():
    if common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_LOGIN")
    data = flask.request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')
    user = pass_auth.get_user(username, password)
    if user:
        flask.session['password_verified'] = {
            'timestamp': int(time.time()),
            'user_id': str(user.id),
            'mobile': user.info.get('mobile', ''),
        }
        if pass_auth.should_start_phone_verify(user, flask.request):
            common.record_login(str(user.id), 'password-sms', **flask.request.headers)
            return api_base.send_json_result("USER_NEED_SMS_AUTH", {})
        else:
            common.login(user, flask.request, flask.session)
            common.record_login(str(user.id), 'password-succ', **flask.request.headers)
            return api_base.send_json_result("SUCC")
    else:
        if 'password_verified' in flask.session:
            del flask.session['password_verified']
        return api_base.send_json_result("USER_NAME_OR_PWD_ERROR")


@pauli_root.route('/auth/api/pass/code', methods=['GET'])
def pass_send_code():
    if common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_LOGIN")
    method = flask.request.args.get('method') or 'voice'
    succ, reason = pass_auth.send_sms_code(flask.session, method=method)
    if succ:
        return api_base.send_json_result("SUCC", {})
    else:
        return api_base.send_json_result("PARAM", msg=reason)


@pauli_root.route('/auth/api/pass/code', methods=['POST'])
def pass_verify_code():
    if common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_LOGIN")
    data = flask.request.get_json(force=True)
    code = data.get('code')
    succ, user = pass_auth.verify_sms_code(flask.session, code)
    if succ:
        common.login(user, flask.request, flask.session)
        common.record_login(str(user.id), 'sms-succ', **flask.request.headers)
        return api_base.send_json_result("SUCC", {})
    else:
        return api_base.send_json_result("USER_VERIFY_CODE_ERROR")


@pauli_root.route('/auth/api/pass/change', methods=['POST'])
def change():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    data = flask.request.get_json(force=True)
    password = data.get('password')
    new_password = data.get('new_password')
    if not (password and new_password):
        return api_base.send_json_result("PARAM")
    username = pass_auth.get_username(flask.request.user)
    if not username:
        return api_base.send_json_result("USER_NAME_OR_PWD_ERROR")
    user = pass_auth.get_user(username, password)
    if user and user.id == flask.request.user.id:
        status, obj = pass_auth.change_password(user, new_password)
        if not status:
            return api_base.send_json_result("PARAM", msg=obj)
        else:
            return api_base.send_json_result("SUCC")
    else:
        return api_base.send_json_result("USER_NAME_OR_PWD_ERROR")


@pauli_root.route('/auth/api/pass/create', methods=['POST'])
def create():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:user:create'):
        return api_base.send_json_result("FORBIDDEN")
    data = flask.request.get_json(force=True)
    username = (data.get('username') or '').lower()
    password = data.get('password') or str(uuid.uuid1().hex)
    name = data.get('name')
    mobile = data.get('mobile') or ''
    creator_id = flask.session["user_id"]
    creator_name = flask.request.user.name
    if not (username and password and name):
        return api_base.send_json_result("PARAM", msg="提供的参数不足")
    status, obj, msg = pass_auth.create_user_by_pass(
        username, password, name=name, mobile=mobile,
        creator_id=creator_id, creator_name=creator_name)
    if status:
        return api_base.send_json_result("SUCC", result={'user_id': str(obj.id)})
    else:
        return api_base.send_json_result("PARAM", msg=msg)


@pauli_root.route('/auth/api/pass/reset', methods=['GET'])
def pass_reset_get():
    email = flask.request.args.get('email')
    if not email:
        return api_base.send_json_result("PARAM")
    email_addr_base = pass_auth.get_reset_addr_base(flask.request)
    succ, msg = pass_auth.send_reset_email(email, email_addr_base)
    if succ:
        return api_base.send_json_result("SUCC")
    else:
        return api_base.send_json_result("PARAM", msg=msg)


@pauli_root.route('/auth/api/pass/reset', methods=['PUT'])
def pass_reset_verify():
    data = flask.request.get_json(force=True)
    code = data.get('code')
    if not code:
        return api_base.send_json_result("PARAM")
    succ, msg = pass_auth.verify_reset_code(code)
    if succ:
        return api_base.send_json_result("SUCC")
    else:
        return api_base.send_json_result("PARAM", msg=msg)


@pauli_root.route('/auth/api/pass/reset', methods=['POST'])
def pass_reset():
    data = flask.request.get_json(force=True)
    code = data.get('code')
    password = data.get('password') or ''
    mobile = data.get('mobile') or ''
    if not code:
        return api_base.send_json_result("PARAM")
    succ, msg = pass_auth.reset_record(code, password=password, mobile=mobile)
    if succ:
        return api_base.send_json_result("SUCC")
    else:
        return api_base.send_json_result("PARAM", msg=msg)


if 'token' in getattr(conf, 'LOGIN_METHODS', []):
    from ..ops import token_auth

    @pauli_root.route('/auth/api/token/login', methods=['POST'])
    def token_login():
        if common.is_logined(flask.request, flask.session):
            return api_base.send_json_result("USER_LOGIN")
        data = flask.request.get_json(force=True)
        token = data.get('token')
        user = token_auth.get_user(token, **flask.request.headers)
        if user:
            common.login(user, flask.request, flask.session)
            common.record_login(str(user.id), 'token',
                                sid=flask.session.sid,
                                **flask.request.headers)
            return api_base.send_json_result("SUCC")
        else:
            return api_base.send_json_result("USER_NAME_OR_PWD_ERROR")


if 'cert' in getattr(conf, 'LOGIN_METHODS', []):
    from ..ops import cert_auth

    @pauli_root.route('/auth/api/cert/login', methods=['GET', 'POST'])
    def cert_login():
        if common.is_logined(flask.request, flask.session):
            return api_base.send_json_result("USER_LOGIN")
        user = cert_auth.get_user(**flask.request.headers)
        if user:
            common.login(user, flask.request, flask.session)
            common.record_login(str(user.id), 'cert',
                                sid=flask.session.sid,
                                **flask.request.headers)
            return api_base.send_json_result("SUCC")
        else:
            return api_base.send_json_result("USER_NAME_OR_PWD_ERROR")


if 'dingtalk' in getattr(conf, 'LOGIN_METHODS', []):
    from ..ops.dingtalk_auth import dingtalk_obj

    @pauli_root.route('/auth/api/dingtalk/jsapi_ticket')
    def dingtalk_jsapi_ticket():
        jsapi_ticket = dingtalk_obj.get_jsapi_ticket()
        return api_base.send_json_result("SUCC", result={'jsapi_ticket': jsapi_ticket})
