# coding:utf-8
import re
import time
import uuid
import datetime
import random
import bcrypt
import six
from ... import conf, event, PauliException
from ...util.cache_util import cache_lock
from ..models import User, PasswordLogin, ResetPasswordRecord


try:
    import validate_email

    def is_email_valid(addr):
        return validate_email.validate_email(addr)
except ImportError as e:
    def is_email_valid(addr):
        matched = re.match(r'[^@]+@[^@]+\.[^@]+', addr)
        return True if matched else False


def to_byte(s, encoding='utf-8', errors='strict'):
    if six.PY2:
        return s.encode(encoding, errors=errors)\
               if isinstance(s, unicode) else s
    else:
        return s.encode(encoding, errors=errors)\
               if isinstance(s, six.string_types) else s


def is_password_valid(password):
    if re.match(r"^([a-zA-Z0-9.!@#$%^&*()<>{}\[\]]{4,40})$", password):
        return True
    return False


def get_password_hash(password):
    pass_hash = bcrypt.hashpw(to_byte(password), bcrypt.gensalt())
    if not isinstance(pass_hash, six.text_type):
        pass_hash = pass_hash.decode('utf-8')
    return pass_hash


def get_username(user):
    user = user if hasattr(user, 'id')\
           else User.objects(id=user, soft_del=False).first()
    if not user:
        return None
    pass_login = PasswordLogin.objects(user_id=str(user.id), soft_del=False).first()
    if not pass_login:
        return None
    else:
        return pass_login.username


def get_user(username, password):
    pl = PasswordLogin.objects(username=username, soft_del=False).first()
    if not pl:
        return None
    user = User.objects(id=pl.user_id, soft_del=False).first()
    if not user:
        return None
    if not bcrypt.checkpw(to_byte(password), to_byte(pl.password)):
        return None
    return user


def create_user_by_pass(username, password, **kw):
    pl = PasswordLogin.objects(username=username, soft_del=False).first()
    if pl:
        return False, None, '用户已经存在'
    if not is_password_valid(password):
        return False, None, '密码格式不正确'
    if not is_email_valid(username):
        return False, None, "用户名必须为电子邮件地址"
    password_hash = get_password_hash(password)
    name = kw.get('name') or ''
    user = User(name=name)
    user.info['email'] = username
    for k, v in kw.items():
        user.info[k] = v
    user.save()
    pl = PasswordLogin(username=username, password=password_hash,
                       user_id=str(user.id))
    pl.save()
    return True, user, ''


def attach_pass_login_to_user(user, username, password):
    if not is_password_valid(password):
        return False, None, '密码格式不正确'
    if not is_email_valid(username):
        return False, None, '用户名必须为Email'
    pl = PasswordLogin.objects(username=username, soft_del=False).first()
    if pl:
        return False, None, '用户登录方式已经存在'
    password_hash = get_password_hash(password)
    user.info['email'] = username
    user.save()
    pl = PasswordLogin(username=username, password=password_hash,
                       user_id=str(user.id))
    pl.save()
    return True, user, ''


def change_password(user, new_password):
    pl = PasswordLogin.objects(user_id=str(user.id), soft_del=False).first()
    if not pl:
        return False, '用户密码不存在'
    if not is_password_valid(new_password):
        return False, '密码格式不正确'
    pl.password = get_password_hash(new_password)
    pl.save()
    return True, ''


def should_start_phone_verify(user, request):
    need_phone_verify = getattr(conf, 'NEED_PHONE_VERIFY', 'optional')
    if need_phone_verify == 'force':
        return True
    elif need_phone_verify == 'optional':
        return True if user.info.get('mobile') else False
    elif need_phone_verify == 'ip':
        ip_list = getattr(conf, 'NEED_PHONE_VERIFY_IP_WHITELIST', [])
        if request.remote_addr in ip_list:
            return False
        else:
            return True
    else:
        return False


def send_sms_code(session, method='voice'):
    password_verified = session.get('password_verified') or {}
    if not password_verified or\
            not (int(time.time()) - password_verified.get('timestamp', 0)) < 25 * 60:
        return False, "用户名/密码未验证或已失效，请返回重新验证"

    mobile = password_verified.get('mobile')
    user_id = password_verified.get('user_id')
    if not mobile:
        return False, "用户的手机号码不存在，请点击下方'重置手机号或密码'链接进行设置"
    if not user_id:
        return False, "用户信息错误，请重试"

    sms_code = session.get('sms_code')
    if not sms_code or\
            (sms_code and sms_code.get('user_id') != user_id):
        code = ''.join([random.choice('0123456789') for i in range(6)])
        sms_code = {'code': code,
                    'user_id': user_id,
                    'timestamp': int(time.time())}
    elif int(time.time()) - sms_code.get('timestamp') > 20 * 60:
        code = ''.join([random.choice('0123456789') for i in range(6)])
        sms_code['code'] = code
    elif int(time.time()) - sms_code.get('timestamp') < 60:
        return False, "验证码发送间隔时间太短"
    else:
        code = sms_code['code']
    if method in ['voice', 'sms']:
        try:
            event.default.send(method,
                               **{"mobile": mobile,
                                  "code": code})
        except PauliException as e:
            return False, e.args[0]
    else:
        return False, "不支持的验证发送方式"

    sms_code['timestamp'] = int(time.time())
    session['sms_code'] = sms_code
    return True, ''


def verify_sms_code(session, code):
    password_verified = session.get('password_verified')
    sms_code = session.get('sms_code')
    if not (sms_code and password_verified):
        return False, ''
    if sms_code.get('user_id') != password_verified.get('user_id'):
        return False, ''
    if int(time.time()) - sms_code.get('timestamp', 0) > 20 * 60\
            or int(time.time()) - password_verified.get('timestamp', 0) > 25 * 60:
        return False, ''
    if not (code and sms_code.get('code')):
        return False, ''
    ret = sms_code.get('code') == code
    if not ret:
        return False, ''
    user = User.objects(id=sms_code['user_id']).first()
    if not user:
        return False, ''
    return True, user

RESET_TEMPLATE = '''您好，
您发起的密码或者安全手机重置操作，请访问 %s%s 。
如果您没有手动发起这个操作，请直接忽略。
'''


def get_reset_addr_base(request):
    referrer = request.referrer or ''
    if not referrer:
        return "https://gbm.gstianfu.com/static/gbm/#/resetpwd?code="
    idx = referrer.find('#')

    if idx != -1:
        return referrer[:idx] + '#/resetpwd?code='
    else:
        return referrer + '#/resetpwd?code='


def send_reset_email(email_addr, reset_addr_base):
    pl = PasswordLogin.objects(username=email_addr, soft_del=False).first()
    if not pl:
        return False, '用户信息错误'
    user = User.objects(id=pl.user_id, soft_del=False).first()
    if not user:
        return False, '用户信息错误'
    curr = int(time.time())
    record_count = ResetPasswordRecord.objects(timestamp__gt=(curr - 86400),
                                               state__ne='used',
                                               user_id=str(user.id)).count()
    if record_count >= 50:
        return False, '24小时内重置次数超过阈值'
    code = uuid.uuid1().hex + uuid.uuid4().hex
    record = ResetPasswordRecord(code=code,
                                 user_id=str(user.id),
                                 state='created')
    record.save()
    event.default.send("reset-email",
                       **{"email_addr": email_addr,
                          "reset_addr_base": reset_addr_base,
                          "code": code})
    return True, record


def verify_reset_code(code, **kw):
    with cache_lock(code):
        curr = int(time.time())
        record = ResetPasswordRecord.objects(code=code,
                                             state='created',
                                             timestamp__gt=(curr - 86400)).first()
        if record:
            record.query_times += 1
            if 'verifies' not in record.info:
                record.info['verifies'] = []
            entry = {'timestamp': curr,
                     'date': str(datetime.datetime.now())}
            entry.update(kw)
            record.info['verifies'].append(entry)
            record.save()
        if record and record.query_times < 5:
            return True, record
        return False, '重置记录不存在或者已失效'


def reset_record(code, password='', mobile=''):
    with cache_lock(code):
        curr = int(time.time())
        record = ResetPasswordRecord.objects(code=code,
                                             state='created',
                                             timestamp__gt=(curr - 86400)).first()
        if not record:
            return False, '重置记录不存在或者已失效'
        if record.query_times >= 5 or not (password or mobile):
            record.state = 'invalid'
            record.save()
            return False, '重置记录不存在或者已失效'
        user = User.objects(id=record.user_id, soft_del=False).first()
        pl = PasswordLogin.objects(user_id=record.user_id, soft_del=False).first()
        if not user and pl:
            record.state = 'invalid'
            record.save()
            return False, '重置记录不存在或者已失效'
        if mobile:
            if not re.match(r"^[1][3456789][\d]{9}$", mobile):
                return False, '手机号码格式不正确'
            user.info['mobile'] = mobile
            record.info['mobile'] = True
            user.save()
        if password:
            record.info['password'] = True
            change_password(user, password)
        record.state = 'used'
        record.save()
        return True, record
