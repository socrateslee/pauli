# coding:utf-8
import json
import flask
from ...util import api_base
from ...common import pauli_root
from ...user.ops import user_base
from ...auth.ops import common
from ..ops import perm_base
from ..ops import user_perm
from ..ops import position as position_ops
from ..ops.decr import perm_required


@pauli_root.route('/perm/api/perm/list', methods=['GET'])
@perm_required()
def api_perm_list():
    '''
    获取当前或者指定用户的全部权限描述。
    '''
    user_id = flask.request.args.get('user_id')
    exclude_role = True if flask.request.args.get('exclude_role') == '1' else False
    if user_id:
        if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:user:get'):
            return api_base.send_json_result("FORBIDDEN")
    else:
        user_id = flask.session["user_id"]
    perm_list = user_perm.get_user_perm_list(user_id, exclude_role=exclude_role)
    return api_base.send_json_result("SUCC",
                               {'perm_list': perm_list,
                                'user_id': user_id})


@pauli_root.route('/perm/api/perm/has', methods=['POST'])
@perm_required()
def api_perm_has():
    '''
    检查当前用户或者指定用户是否拥有某一权限。
    '''
    data = flask.request.get_json(force=True)
    perm = data.get('perm')
    target_user_id = data.get('target_user_id')
    target_position_id = data.get('target_position_id')
    user_id = data.get('user_id')

    # Deal with query for other users
    if user_id and not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:user:get'):
        return api_base.send_json_result("FORBIDDEN", msg="需要pauli:perm:user:get权限，请联系管理员")
    if not user_id:
        user_id = flask.session["user_id"]

    if not perm:
        has = False
    else:
        is_upstream = position_ops.is_upstream_position(user_id,
                      position_id=target_position_id, user_id=target_user_id)
        is_owner = position_ops.is_owner(user_id,
                   position_id=target_position_id, user_id=target_user_id)
        has = user_perm.has_perm(user_id, perm,
                                 is_upstream=is_upstream, is_owner=is_owner)
    return api_base.send_json_result("SUCC", {'has': has})


@pauli_root.route('/perm/api/perms/has', methods=['POST'])
@perm_required()
def api_perms_has():
    '''
    检查当前用户或者指定用户是否拥有某一个列表的权限
    '''
    data = flask.request.get_json(force=True)
    perms = data.get('perms') or []
    target_user_id = data.get('target_user_id')
    target_position_id = data.get('target_position_id')
    user_id = data.get('user_id')
    return_type = 'list' if data.get('return_type') == 'list' else 'dict'

    # Deal with query for other users
    if user_id and not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:user:get'):
        return api_base.send_json_result("FORBIDDEN", msg="需要pauli:perm:user:get权限，请联系管理员")
    if not user_id:
        user_id = flask.session["user_id"]

    ret = []
    perm_list = user_perm.get_user_perm_list(user_id)
    is_upstream = position_ops.is_upstream_position(user_id,
                  position_id=target_position_id, user_id=target_user_id)
    is_owner = position_ops.is_owner(user_id,
               position_id=target_position_id, user_id=target_user_id)

    for perm in perms:
        has = user_perm.has_perm(user_id, perm,
                                 is_upstream=is_upstream,
                                 is_owner=is_owner,
                                 perm_list=perm_list)
        ret.append((perm, has))
    ret = dict(ret) if return_type == 'dict' else ret
    return api_base.send_json_result("SUCC", {'perms': ret})


@pauli_root.route('/perm/api/perm/triple', methods=['GET'])
@perm_required()
def api_perm_triple():
    perm_action = flask.request.args.get('action')
    if not perm_action:
        return api_base.send_json_result("PARAM", msg="必须提供参数action")
    succ, triples = user_perm.get_perm_triples([perm_action], flask.session['user_id'])
    if not succ:
        return api_base.send_json_result("PARAM", msg=triples)
    triple = triples[perm_action]
    if triple.get('+') == True:
        triple['+'] = list(position_ops.get_all_granted_position_ids(flask.session['user_id']))
    if triple.get('-') == True and flask.request.user.info.get('position_id'):
        triple['-'] = flask.session['user_id']
    else:
        triple['-'] = False
    return api_base.send_json_result("SUCC", {'triple': triple})


@pauli_root.route('/perm/api/perm/triples', methods=['POST'])
@perm_required()
def api_perm_triples():
    data = flask.request.get_json(force=True)
    perm_actions = data.get('actions')
    if not perm_actions:
        return api_base.send_json_result("PARAM", msg="必须提供参数actions")
    succ, triples = user_perm.get_perm_triples(perm_actions, flask.session['user_id'])
    if not succ:
        return api_base.send_json_result("PARAM", msg=triple)
    position_ids = list(position_ops.get_all_granted_position_ids(flask.session['user_id']))
    for action in triples:
        triple = triples[action]
        if triple.get('+') == True:
            triple['+'] = position_ids
        if triple.get('-') == True and flask.request.user.info.get('position_id'):
            triple['-'] = flask.session['user_id']
        else:
            triple['-'] = False
    return api_base.send_json_result("SUCC", {'triples': triples})


@pauli_root.route('/perm/api/perm/user/add', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_perm_grant_to_user():
    data = flask.request.get_json(force=True)
    perm = data.get('perm')
    target_user_id = data.get('user_id')
    if not (perm and target_user_id):
        return api_base.send_json_result("PARAM")
    succ, obj = user_perm.add_perm(perm, user_id=target_user_id)
    if succ:
        return api_base.send_json_result("SUCC", {'perm_list': obj.perms})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/user/update', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_perm_user_upadte():
    data = flask.request.get_json(force=True, silent=True) or {}
    perm = data.get('perms')
    target_user_id = data.get('user_id')
    if not (perms and target_user_id):
        return api_base.send_json_result("PARAM")
    succ, obj = user_perm.update_perms(perms, user_id=target_user_id)
    if succ:
        return api_base.send_json_result("SUCC", {'perm_list': obj.perms})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/user/del', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_remove_perm_from_user():
    data = flask.request.get_json(force=True)
    perm = data.get('perm')
    target_user_id = data.get('user_id')
    succ, obj = user_perm.remove_perm(perm, user_id=target_user_id)
    if succ:
        return api_base.send_json_result("SUCC", {'perm_list': obj.perms})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/user/position', methods=['GET'])
def api_get_user_position():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    user_id = flask.request.args.get("user_id")
    if user_id and not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:user:get'):
        return api_base.send_json_result("FORBIDDEN", msg="用户没有权限pauli:perm:user:get")
    user_id = user_id or flask.session['user_id']
    positions = list(position_ops.get_granted_position_ids(user_id,
                                                           include_roles=False))
    return api_base.send_json_result("SUCC", result={'positions': positions})


@pauli_root.route('/perm/api/perm/user/position', methods=['POST'])
@perm_required("pauli:perm:user:update")
def api_set_user_position():
    data = flask.request.get_json(force=True)
    user_id = data.get('user_id')
    position_id = data.get('position_id')
    if not user_id:
        return api_base.send_json_result("PARAM", msg="user_id未提供")
    status, obj = position_ops.set_position(user_id, position_id)
    if status:
        return api_base.send_json_result("SUCC", result={'position_id': obj.position_id})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/user/position/grant', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_grant_user_position():
    data = flask.request.get_json(force=True)
    user_id = data.get('user_id')
    position_id = data.get('position_id')
    if not (user_id and position_id):
        return api_base.send_json_result("PARAM",
                msg="user_id或者position_id未提供")
    status, obj = position_ops.grant_position('add', position_id, user_id=user_id)
    if status:
        return api_base.send_json_result("SUCC", result={'grant_positions': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/user/position/recall', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_recall_user_position():
    data = flask.request.get_json(force=True)
    user_id = data.get('user_id')
    position_id = data.get('position_id')
    if not (user_id and position_id):
        return api_base.send_json_result("PARAM",
                msg="user_id或者position_id未提供")
    status, obj = position_ops.grant_position('del', position_id, user_id=user_id)
    if status:
        return api_base.send_json_result("SUCC", result={'grant_positions': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/user/position/update', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_update_user_positions():
    data = flask.request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    position_ids = data.get('position_ids')
    if not (user_id and position_ids):
        return api_base.send_json_result("PARAM",
                                   msg="user_id或者position_ids未提供")
    if not type(position_ids) is list:
        return api_base.send_json_result("PARAM",
                                   msg="position_ids必须为list")
    status, obj = position_ops.set_granted_positions(user_id, position_ids)
    if status:
        return api_base.send_json_result("SUCC",
                                   result={'grant_positions': obj.granted_positions})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/role/position/grant', methods=['PUT'])
@perm_required("pauli:perm:role:update")
def api_grant_role_position():
    data = flask.request.get_json(force=True)
    role_id = data.get('role_id')
    position_id = data.get('position_id')
    if not (role_id and position_id):
        return api_base.send_json_result("PARAM",
                msg="role_id或者position_id未提供")
    status, obj = position_ops.grant_position('add', position_id, role_id=role_id)
    if status:
        return api_base.send_json_result("SUCC", result={'grant_positions': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/role/position/recall', methods=['PUT'])
@perm_required("pauli:perm:role:update")
def api_recall_role_position():
    data = flask.request.get_json(force=True)
    role_id = data.get('role_id')
    position_id = data.get('position_id')
    if not (role_id and position_id):
        return api_base.send_json_result("PARAM",
                msg="role_id或者position_id未提供")
    status, obj = position_ops.grant_position('del', position_id, role_id=role_id)
    if status:
        return api_base.send_json_result("SUCC", result={'grant_positions': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/role/add', methods=['PUT'])
def api_grant_perm_to_role():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role:update'):
        return api_base.send_json_result("FORBIDDEN")
    data = flask.request.get_json(force=True)
    perm = data.get('perm')
    target_role_id = data.get('role_id')
    if not (perm and target_role_id):
        return api_base.send_json_result("PARAM")
    succ, obj = user_perm.add_perm(perm, role_id=target_role_id)
    if succ:
        return api_base.send_json_result("SUCC", result={'perm_list': obj.perms})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/perm/role/del', methods=['PUT'])
def api_remove_perm_from_role():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role:update'):
        return api_base.send_json_result("FORBIDDEN")
    data = flask.request.get_json(force=True)
    perm = data.get('perm')
    target_role_id = data.get('role_id')
    succ, obj = user_perm.remove_perm(perm, role_id=target_role_id)
    if succ:
        return api_base.send_json_result("SUCC", result={'perm_list': obj.perms})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/role/list', methods=['GET'])
def api_role_list():
    '''
    获取全部角色列表。
    '''
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role'):
        return api_base.send_json_result("FORBIDDEN")
    roles = user_perm.get_all_roles()
    roles_list = map(lambda x: {'id': str(x.id), 'name': x.name}, roles)
    return api_base.send_json_result("SUCC", result={'roles': list(roles_list)})


@pauli_root.route('/perm/api/role', methods=['GET'])
def api_get_role():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role:get'):
        return api_base.send_json_result("FORBIDDEN")
    role_id = flask.request.args.get('role_id')
    succ, obj = user_perm.get_role_info(role_id=role_id)
    if succ:
        return api_base.send_json_result("SUCC", result={'role': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/role', methods=['POST'])
def api_create_role():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role:create'):
        return api_base.send_json_result("FORBIDDEN")
    data = flask.request.get_json(force=True)
    name = data.get('name')
    succ, obj = user_perm.create_role(name=name)
    if succ:
        return api_base.send_json_result("SUCC", result={'role': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/role', methods=['DELETE'])
def api_remove_role():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role:del'):
        return api_base.send_json_result("FORBIDDEN")
    role_id = flask.request.args.get('role_id')
    succ, obj = user_perm.remove_role(role_id)
    if succ:
        return api_base.send_json_result("SUCC", result={'role': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/role', methods=['PUT'])
def api_update_role():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:role:update'):
        return api_base.send_json_result("FORBIDDEN")
    data = flask.request.get_json(force=True)
    role_id = data.get('role_id')
    name = data.get('name')
    succ, obj = user_perm.update_role(role_id, name=name)
    if succ:
        return api_base.send_json_result("SUCC", result={'role': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/role/user/list', methods=['GET'])
def api_get_role_list():
    '''
    获取当前或者指定用户的角色id列表。
    '''
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    user_id = flask.request.args.get('user_id')
    if user_id and not user_perm.has_perm(flask.session["user_id"],
                                          'pauli:perm:user:get'):
        return api_base.send_json_result("FORBIDDEN", msg="用户没有权限pauli:perm:user:get")
    if not user_id:
        user_id = flask.session['user_id']
    roles = user_perm.get_user_roles(user_id)
    roles_list = map(lambda x: {'id': str(x.id), 'name': x.name}, roles)
    return api_base.send_json_result("SUCC", result={'roles': list(roles_list)})


@pauli_root.route('/perm/api/role/user/update', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_update_user_role():
    data = flask.request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    role_ids = data.get('role_ids') or []
    if not (user_id and role_ids):
        return api_base.send_json_result("FORBIDDEN")
    succ, obj = user_perm.update_user_roles(user_id, role_ids)
    if succ:
        roles = user_perm.get_user_roles(user_id)
        roles_list = list(map(lambda x: {'id': str(x.id), 'name': x.name}, roles))
        return api_base.send_json_result("SUCC",
                                   result={'roles': roles_list})
    else:
        return api_base.send_json_result("PARAM",
                                   msg=obj)


@pauli_root.route('/perm/api/role/user', methods=['PUT'])
@perm_required("pauli:perm:user:update")
def api_grant_role_to_user():
    data = flask.request.get_json(force=True)
    role_id = data.get('role_id')
    user_id = data.get('user_id')
    succ, obj = user_perm.add_role_to_user(role_id, user_id)
    if succ:
        roles = user_perm.get_user_roles(user_id)
        roles_list = list(map(lambda x: {'id': str(x.id), 'name': x.name}, roles))
        return api_base.send_json_result("SUCC", result={'roles': roles_list})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/role/user', methods=['DELETE'])
def api_remove_role_from_user():
    if not common.is_logined(flask.request, flask.session):
        return api_base.send_json_result("USER_NOT_LOGIN")
    if not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:user:update'):
        return api_base.send_json_result("FORBIDDEN", msg="用户没有权限pauli:perm:user:update")
    role_id = flask.request.args.get('role_id')
    user_id = flask.request.args.get('user_id')
    succ, obj = user_perm.remove_role_from_user(role_id, user_id)
    if succ:
        roles = user_perm.get_user_roles(user_id)
        roles_list = list(map(lambda x: {'id': str(x.id), 'name': x.name}, roles))
        return api_base.send_json_result("SUCC", result={'roles': roles_list})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/position/users', methods=['GET', 'POST'])
@perm_required()
def api_position_users():
    position_ids = []
    if flask.request.method == "GET":
        position_id = flask.request.args.get('position_id')
        if position_id:
            position_ids.append(position_id)
    elif flask.request.method == "POST":
        data = flask.request.get_json(force=True)
        position_ids = data.get('position_ids') or []
    if not position_ids:
        granted_position_ids = list(position_ops.get_granted_position_ids(flask.session["user_id"]))
    else:
        if not position_ops.is_upstream_position(flask.request.user,
                                                 position_ids=position_ids)\
                and not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:position:list'):
            return api_base.send_json_result("FORBIDDEN", msg="用户不是所传职位的上级用户")
        granted_position_ids = position_ids
    users = position_ops.get_users_by_sub_positions(granted_position_ids, included=True)
    ret = [user_base.to_dict(user) for user in users]
    return api_base.send_json_result("SUCC", result={'users': ret})


@pauli_root.route('/perm/api/position/list', methods=['GET', 'POST'])
@perm_required()
def api_position_list():
    position_ids = []
    if flask.request.method == "GET":
        position_id = flask.request.args.get('position_id')
        if position_id:
            position_ids.append(position_id)
    elif flask.request.method == "POST":
        data = flask.request.get_json(force=True)
        position_ids = data.get('position_ids') or []
    if not position_ids:
        all_position_ids = list(position_ops.get_all_granted_position_ids(flask.session["user_id"]))
    else:
        if not position_ops.is_upstream_position(flask.request.user,
                                                 position_ids=position_ids)\
                and not user_perm.has_perm(flask.session["user_id"], 'pauli:perm:position:list'):
            return api_base.send_json_result("FORBIDDEN", msg="用户不是所传职位的上级用户")
        all_positions = position_ops.get_sub_positions(position_ids, included=True)
        all_position_ids = list(map(lambda x: str(x.id), all_positions))
    return api_base.send_json_result("SUCC", result={'position_list': all_position_ids})


@pauli_root.route('/perm/api/position/leaders/info', methods=['GET'])
@perm_required()
def api_position_leaders_info():
    '''
    获取一个团队的leader的info.
    '''
    position_id = flask.request.args.get('position_id') or ''
    if not position_id:
        return api_base.send_json_result("PARAM",
                                   msg="必须传递position_id")
    user_ids = position_ops.get_position_leaders(position_id)
    succ, obj = user_base.get_user_info_dict(user_ids)
    if succ:
        return api_base.send_json_result("SUCC", {'info': obj})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/position/tree', methods=['GET'])
@perm_required()
def api_position_tree():
    extend = True if flask.request.args.get('extend') else False
    position_id = flask.request.args.get('position_id')
    if position_id:
        if user_perm.has_perm(flask.session["user_id"], 'pauli:perm:position:list'):
            granted_position_ids = [position_id]
        else:
            return api_base.send_json_result("FORBIDDEN", msg="用户不是所传职位的上级用户")
    else:
        granted_position_ids = position_ops.get_granted_position_ids(flask.session["user_id"])
    ret = position_ops.position_tree(granted_position_ids, extend_users=extend)
    return api_base.send_json_result("SUCC", result={'tree': ret})


@pauli_root.route('/perm/api/position/dump', methods=['GET'])
@perm_required(perms="pauli:perm:position:dump")
def api_position_dump():
    ret = position_ops.position_tree_dump()
    return api_base.send_json_result("SUCC", result={'dump': ret})


@pauli_root.route('/perm/api/position', methods=['GET'])
@perm_required()
def api_position_get():
    position_id = flask.request.args.get("position_id")
    if not position_id:
        return api_base.send_json_result("PARAM")
    position_info = position_ops.get_position_info(position_id)
    return api_base.send_json_result("SUCC",
               result={'position': position_info})


@pauli_root.route('/perm/api/positions', methods=['PUT'])
@perm_required()
def api_positions_get():
    data = flask.request.get_json(force=True)
    position_ids = data.get('position_ids')
    if not position_ids:
        return api_base.send_json_result("PARAM")
    position_info_dict = {}
    for position_id in position_ids:
        position = position_ops.get_position_info(position_id)
        if position:
            position_info_dict[position_id] = position
    return api_base.send_json_result("SUCC",
               result={'positions': position_info_dict})


@pauli_root.route('/perm/api/position', methods=['POST'])
@perm_required(perms="pauli:perm:position:add")
def api_position_add():
    data = flask.request.get_json(force=True)
    name = data.get('name')
    parent_id = data.get('parent_id') or None
    parent_name = data.get('parent_name') or None
    if not name:
        return api_base.send_json_result("PARAM", msg="未提供职位或者团队的name")
    status, obj = position_ops.add_position(name,
                                            parent_id=parent_id,
                                            parent_name=parent_name)
    if status:
        return api_base.send_json_result("SUCC",
                result={'position': position_ops.position_to_dict(obj)})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/position', methods=['DELETE'])
@perm_required(perms="pauli:perm:position:delete")
def api_position_delete():
    position_id = flask.request.args.get('position_id')
    if not position_id:
        return api_base.send_json_result("PARAM", msg="未提供职位或者团队id")
    status, obj = position_ops.remove_position(position_id)
    if status:
        return api_base.send_json_result("SUCC",
                result={'position': position_ops.position_to_dict(obj)})
    else:
        return api_base.send_json_result("PARAM", msg=obj)


@pauli_root.route('/perm/api/position', methods=['PUT'])
@perm_required(perms="pauli:perm:position:update")
def api_position_update():
    data = flask.request.get_json(force=True)
    position_id = data.get('position_id')
    new_name = data.get('new_name') or ''
    parent_id = data.get('parent_id')

    if position_id and new_name:
        status, obj = position_ops.rename_position(position_id,
                      new_name)
    elif position_id and parent_id is not None:
        status, obj = position_ops.move_position(position_id,
                      target_parent_id=parent_id)
    else:
        return api_base.send_json_result("PARAM", msg="未提供职位或者团队id")
    if status:
        return api_base.send_json_result("SUCC",
                result={'position': position_ops.position_to_dict(obj)})
    else:
        return api_base.send_json_result("PARAM", msg=obj)
