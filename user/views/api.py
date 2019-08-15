# coding:utf-8
import json
import flask
from mongoengine import Q
from ...util import api_base
from ...common import pauli_root
from ..ops import user_base
from ...auth.ops import common
from ...perm.ops import user_perm
from ...perm.ops.decr import perm_required


@pauli_root.route('/user/api/list', methods=['GET'])
@perm_required()
def api_user_list():
    '''
    获取全部用户列表，不包括已经删除的用户
    '''
    keyword = flask.request.args.get('keyword') or ''
    enabled = flask.request.args.get('enabled') or ''
    if enabled in ['0', '1']:
        query = {'soft_del': {'1': False, '0': True}[enabled]}
    else:
        query = {'soft_del__in': [False, True]}
    keywords = [i.strip() for i in keyword.split() if i.strip()]
    if keywords:
        query['keywords__in'] = keywords
    succ, obj = user_base.list_users(q=query)
    if succ:
        return api_base.send_json_result("SUCC", {'user_list': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/info/update', methods=['PUT'])
@perm_required("pauli:user:update")
def api_user_info_update():
    '''
    更新用户信息
    '''
    data = flask.request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    name = data.get('name')
    if not (user_id and name):
        return api_base.send_json_result("PARAM", msg='必须提供user_id')
    succ, obj = user_base.update_user(user_id, name=name)
    if succ:
        return api_base.send_json_result("SUCC", {'user': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/info', methods=['POST'])
@perm_required()
def api_user_info():
    '''
    根据id获取用户的名字
    '''
    data = flask.request.get_json(force=True)
    user_ids = data.get("user_ids")
    if not user_ids:
        return api_base.send_json_result("PARAM", msg="必须传递用户id列表")
    succ, obj = user_base.get_user_info_dict(user_ids)
    if succ:
        return api_base.send_json_result("SUCC", {'info': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/names', methods=['POST'])
@perm_required()
def api_user_names():
    '''
    根据id获取用户的名字
    '''
    data = flask.request.get_json(force=True)
    user_ids = data.get("user_ids")
    if not user_ids:
        return api_base.send_json_result("PARAM", msg="必须传递用户id列表")
    succ, obj = user_base.get_user_names(user_ids)
    if succ:
        return api_base.send_json_result("SUCC", {'user_names': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/query', methods=['GET'])
@perm_required("pauli:user:list")
def api_user_query():
    '''
    根据用户名或者用户姓名等信息筛选相关用户，包括已经disabled掉的用户
    '''
    keyword = flask.request.args.get('keyword')
    if not keyword:
        return api_base.send_json_result("PARAM")
    succ, obj = user_base.query_users(keyword)
    if succ:
        return api_base.send_json_result("SUCC", {'user_list': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/query/byinfo', methods=['GET'])
@perm_required()
def api_user_query_by_info():
    '''
    根据用户info中的信息查询用户列表，仅限email、mobile和role_name
    '''
    query_type = flask.request.args.get('query_type')
    query_value = flask.request.args.get('query_value')
    if query_type not in ['email', 'mobile', 'role_name'] or not query_value:
        return api_base.send_json_result("PARAM")
    query = user_base.query_by_info(query_type, query_value)
    users = [user_base.to_dict(user) for user in query]
    return api_base.send_json_result("SUCC", {'users': users})


@pauli_root.route('/user/api/get/byinfo', methods=['GET'])
@perm_required()
def api_user_get_by_info():
    '''
    根据用户info中的信息查询单个用户，仅限email和mobile
    '''
    query_type = flask.request.args.get('query_type')
    query_value = flask.request.args.get('query_value')
    if query_type not in ['email', 'mobile'] or not query_value:
        return api_base.send_json_result("PARAM")
    succ, obj = user_base.get_by_info(query_type, query_value)
    if succ:
        return api_base.send_json_result("SUCC", {'user': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/enabled', methods=['GET'])
@perm_required("pauli:user:update")
def api_user_enable():
    '''
    使停用的用户恢复成enabled状态.
    '''
    user_id = flask.request.args.get('user_id')
    if not user_id:
        return api_base.send_json_result("PARAM")
    status, obj = user_base.enable_user(user_id)
    if status:
        return api_base.send_json_result("SUCC", result={'user': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/enabled', methods=['DELETE'])
@perm_required("pauli:user:update")
def api_user_disable():
    '''
    停用现有用户.
    '''
    user_id = flask.request.args.get('user_id')
    if not user_id:
        return api_base.send_json_result("PARAM")
    status, obj = user_base.disable_user(user_id)
    if status:
        return api_base.send_json_result("SUCC", result={'user': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/user/api/audit', methods=['GET'])
@perm_required("pauli:user:audit")
def api_user_audit():
    '''
    获取用户的audit log
    '''
    user_id = flask.request.args.get('user_id')
    cursor_id = flask.request.args.get('cursor_id') or ''
    limit = int(flask.request.args.get('limit') or 10)
    if not user_id:
        return api_base.send_json_result("PARAM")
    status, obj = user_base.get_user_audit_log(user_id,
                                               cursor_id=cursor_id,
                                               limit=limit)
    if status:
        return api_base.send_json_result("SUCC", result={'logs': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)
