# coding:utf-8
import datetime
from mongoengine import *
from ..util import db as db_util
from ..user.models import UserAuditLog


@db_util.change_lut_on_save
class PermDesc(Document):
    '''
    权限的描述，用于权限列表的展示，权限的提示等
    '''
    meta = {"db_alias": "pauli",
            "indexes": ['action', 'name']}
    action = StringField()
    effect = StringField(default="allow")
    resources = ListField()
    name = StringField()
    created = DateTimeField(default=datetime.datetime.now)
    soft_del = BooleanField(default=False)
    lut = DateTimeField(default=datetime.datetime.now)


@db_util.change_lut_on_save
class RoleDesc(Document):
    meta = {"db_alias": "pauli",
            "indexes": []}
    name = StringField()
    perms = ListField()
    granted_positions = ListField()
    created = DateTimeField(default=datetime.datetime.now)
    soft_del = BooleanField(default=False)
    lut = DateTimeField(default=datetime.datetime.now)


@db_util.change_lut_on_save
class PositionDesc(Document):
    '''
    职位描述，每个用户通过关联职位描述来确定上下级关系和数据集权限
    --------
    name: string, 职位名称
    parent_id: string, 职位的父级职位id
    path: list, 从根节点到当前节点的id路径，包括根节点，不包括当前节点
    position_type: string, 职位的类型，用于区分一些特殊的职位，比如理财顾问
    '''
    meta = {"db_alias": "pauli",
            "indexes": ['parent_id', 'path', 'name']}
    name = StringField()
    parent_id = StringField(default='')
    path = ListField()
    position_type = StringField(default='')
    created = DateTimeField(default=datetime.datetime.now)
    soft_del = BooleanField(default=False)
    lut = DateTimeField(default=datetime.datetime.now)


@db_util.change_lut_on_save
class UserPerm(Document):
    meta = {"db_alias": "pauli",
            "indexes": ['user_id', 'position_id', 'granted_positions']}
    user_id = StringField()
    roles = ListField()
    perms = ListField()
    position_id = StringField()
    granted_positions = ListField()
    created = DateTimeField(default=datetime.datetime.now)
    soft_del = BooleanField(default=False)
    lut = DateTimeField(default=datetime.datetime.now)

    def save(self):
        UserAuditLog.record(self)
        Document.save(self)
