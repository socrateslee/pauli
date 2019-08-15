# coding:utf-8
import re
import time
import uuid
import random
from ..models import User, TokenLogin


def get_user(token, **headers):
    if 'X-Forwarded-For' in headers or 'X-Forwarded-Proto' in headers:
        return None
    token_login = TokenLogin.objects(token=token, soft_del=False).first()
    if not token_login:
        return None
    user = User.objects(id=token_login.user_id, soft_del=False).first()
    return user


def attach_token_login(user):
    user = User.objects(id=user).first()\
           if not hasattr(user, 'id') else user
    if not (user and not user.soft_del):
        return False, '用户不存在'
    token_login = TokenLogin.objects(user_id=str(user.id), soft_del=False).first()
    if token_login:
        return True, token_login
    token_login = TokenLogin(user_id=str(user.id), token=str(uuid.uuid1()))
    token_login.save()
    return True, token_login


def revoke_token(token):
    token_login = TokenLogin.objects(token=token, soft_del=False).first()
    if token:
        token_login.soft_del = True
        token_login.save()
        return True
    return False
