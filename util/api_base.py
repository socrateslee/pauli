# -*- coding: utf-8 -*-
'''
Provide basic utilities for api.
'''
import json
import flask


STATUS_CODES = {
    'E_SUCC': (0, '成功'),
    'E_PARAM': (1, '参数错误'),
    'E_INTER': (2, '程序内部错误'),
    'E_EXTERNAL': (3, '外部接口错误'),
    'E_TIMEOUT': (4, '第三方接口超时'),
    'E_RESRC': (5, '接口不存在'),
    'E_AUTH': (6, '鉴权失败'),
    'E_FORBIDDEN': (7, '访问被禁止'),
    'E_RESOURCE_NOT_FIND': (8, '资源不存在或已删除'),
    'E_USER_NOT_EXIST_IN_CRM': (1024, 'CRM系统中不存在该用户'),
    'E_USER_LOCKED': (1000, '用户被锁定'),
    'E_USER_EXIST': (1001, '该手机号已被注册'),
    'E_USER_NOT_EXIST': (1002, '用户不存在, 请检查手机号码是否正确，或者前往注册'),
    'E_USER_LOGIN': (1003, '用户已登录'),
    'E_USER_NOT_LOGIN': (1004, '用户未登录'),
    'E_USER_NAME_OR_PWD_ERROR': (1005, '手机号码与密码不匹配'),
    'E_USER_VERIFY_CODE_LOCKED': (1006, '请不要在60秒内连续发送验证码'),
    'E_USER_VERIFY_CODE_ERROR': (1007, '验证码错误，请输入正确的验证码'),
    'E_USER_LOGIN_PWD_NOT_SET': (1008, '账户未设置过密码，请使用验证码登录'),
    'E_USER_HEAD_UPLOAD_ERROR': (1010, '头像上传失败'),
    'E_USER_AUTH_PWD_VERIFY_RETRY': (1011, '密码验证错误'),
    'E_USER_AUTH_PWD_VERIFY_ERROR': (1012, '密码验证失败，您将退出登录'),
    'E_USER_PHONE_NUMBER_ERROR': (1013, '手机号格式错误'),
    'E_USER_IDENTITY_CARD_ERROR': (1014, '身份证号码不合法'),
    'E_USER_BANK_CARD_ERROR': (1015, '银行卡号不合法'),
    'E_USER_MODIFY_RISK_ERROR': (1016, '提交风险承受能力失败'),
    'E_USER_BUS_TYPE_INVALID': (1017, '验证业务类型不匹配'),
    'E_USER_AUTH_TOKEN_INVALID': (1018, '鉴权令牌已失效，请重新发送验证码'),
    'E_USER_AUTH_TOKEN_ERROR': (1019, '鉴权令牌校验失败'),
    'E_USER_AUTH_NOT_EXIST': (1020, '手机号码不存在，无法获取验证码'),
    'E_USER_AUTH_PWD_VERIFY_INVALID': (1021, '密码格式不正确'),
    'E_USER_ORG_LOGIN_PWD_ERROR': (1022, '原登录密码错误'),
    'USER_NEED_SMS_AUTH': (1023, '需要进行短信验证')
}


def send_json_result(code, result=None, msg=None):
    sc_code = 'E_%s' % code if isinstance(code, str) else code
    status = STATUS_CODES.get(sc_code)
    ret = json.dumps({'code': status[0],
                      'result': {} if result is None else result,
                      'msg': msg or status[1]})
    resp = flask.Response(ret)
    resp.content_type = 'application/json'
    return resp
