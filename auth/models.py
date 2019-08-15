import time
import datetime
from ..util import db as db_util
from mongoengine import *
from ..user.models import User, UserAuditLog


@db_util.change_lut_on_save
class PasswordLogin(Document):
    meta = {"db_alias": "pauli",
            "indexes": ['user_id', 'username']}
    user_id = StringField(required=True)
    username = StringField(required=True)
    password = StringField()
    soft_del = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now)
    lut = DateTimeField(default=datetime.datetime.now)

    def save(self):
        UserAuditLog.record(self)
        Document.save(self)


@db_util.change_lut_on_save
class ResetPasswordRecord(Document):
    meta = {"db_alias": "pauli",
            "indexes": ['user_id', 'code']}
    user_id = StringField()
    code = StringField()
    query_times = IntField(default=0)
    state = StringField(choices=['created', 'invalid', 'used'],
                        default='created')
    info = DictField()
    timestamp = IntField(default=lambda: int(time.time()))
    created = DateTimeField(default=datetime.datetime.now)
    lut = DateTimeField(default=datetime.datetime.now)


@db_util.change_lut_on_save
class DingtalkLogin(Document):
    meta = {"db_alias": "pauli",
            "indexes": ['user_id', 'dingtalk_id']}
    user_id = StringField(required=True)
    dingtalk_id = StringField(required=True)
    info = DictField()
    soft_del = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now)
    lut = DateTimeField(default=datetime.datetime.now)


@db_util.change_lut_on_save
class CertLogin(Document):
    '''
    Login via client side ssl certificate.
    Used for server access via public networks.
    '''
    meta = {"db_alias": "pauli",
            "indexes": ['user_id']}
    user_id = StringField(required=True)
    serial = StringField(required=True, unique=True)
    info = DictField()
    soft_del = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now)
    lut = DateTimeField(default=datetime.datetime.now)


@db_util.change_lut_on_save
class TokenLogin(Document):
    '''
    Login via a fixed token in header.
    Used for server access inside a trusted networks.
    '''
    meta = {"db_alias": "pauli",
            "indexes": ['user_id']}
    user_id = StringField(required=True)
    token = StringField(required=True)
    info = DictField()
    soft_del = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now)
    lut = DateTimeField(default=datetime.datetime.now)


class LoginRecord(Document):
    meta = {"db_alias": "pauli",
            "indexes": ['user_id']}
    user_id = StringField(required=True)
    login_type = StringField()
    sid = StringField()
    expiration = DateTimeField()
    info = DictField()
    created = DateTimeField(default=datetime.datetime.now)
