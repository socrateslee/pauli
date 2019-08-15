# coding: utf-8
import time
import uuid
import flask
from ... import conf, pauli_root
from ..ops import common


# 采用用户名密码作为认证方式
if 'password' in conf.LOGIN_METHODS:

    @pauli_root.route('/auth/web/password/login', methods=['GET'])
    def password_login():
        return flask.render_template('password_login.html')

    @pauli_root.route('/auth/web/password/reset', methods=['GET'])
    def password_reset():
        return ''


# 采用dingding作为认证方式
if 'dingtalk' in conf.LOGIN_METHODS:
    from ..ops.dingtalk_auth import dingtalk_obj, get_or_create_dingtalk_user


    @pauli_root.route('/auth/web/dingtalk/config.js', methods=['GET'])
    def dingtalk_config():
        apis = flask.request.args.get('apis') or ''
        api_list = [i.strip() for i in apis.split(',') if i.strip()]
        url = flask.request.referer
        ret = dingtalk_obj.get_dd_config(url, api_list=api_list)
        api_list = ret.pop('jsApiList')
        js_code = ', '.join("%s: '%s'" % (k, v) for k, v in ret.items())
        js_code += ', jsApiList: %s' % str(api_list)
        js_code = 'dd.config({%s})' % js_code
        return flask.Response(js_code, mimetype='application/javascript')


    @pauli_root.route('/auth/web/dingtalk/login', methods=['GET'])
    def dingtalk_login():
        next_url = flask.request.args.get('next')
        if common.is_logined(flask.request, flask.session) and next_url:
            return flask.redirect(next_url)
        url = flask.request.url
        dd_config = dingtalk_obj.get_dd_config(url)
        if 'mobile' in (flask.request.headers.get('User-Agent') or '').lower():
            return flask.render_template('dingtalk_login_mobile.html', dingtalk_data=dd_config)
        return flask.render_template('dingtalk_login.html', dingtalk_data=dd_config)


    @pauli_root.route('/auth/web/dingtalk/success', methods=['GET'])
    def dingtalk_success():
        code = flask.request.args.get('code') or ''
        next_url = flask.request.args.get('next') or ''
        status, obj = dingtalk_obj.getuserinfo(code)
        msg = "登陆失败"
        if status and obj and obj.get('userid'):
            userid = obj['userid']
            status, obj = dingtalk_obj.get_userdetail(userid)
            if status:
                user, login = get_or_create_dingtalk_user(userid, obj)
                if user and login and not user.soft_del:
                    common.login(user, flask.request, flask.session)
                    common.record_login(str(user.id), 'dingtalk', **flask.request.headers)
                    msg = "登陆成功"
                    if next_url:
                        homepath = next_url
                    elif 'mobile' in (flask.request.headers.get('User-Agent') or '').lower():
                        homepath = getattr(conf, 'HOMEPATH_MOBILE', None)
                    else:
                        homepath = getattr(conf, 'HOMEPATH', None)
                    if homepath:
                        return flask.redirect(homepath)
                else:
                    msg += ', 未关联钉钉与系统账户'
        return flask.render_template('dingtalk_success.html', msg=msg)
