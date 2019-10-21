# coding:utf-8
from collections import deque
from mongoengine import Q
from ...util.cache_util import cache_lock
from ...util.chinese import chinese_num_replace
from ..models import PositionDesc, UserPerm, RoleDesc
from ...auth.models import User
from . import user_perm as user_perm_ops


def position_to_dict(position):
    ret = {'id': str(position.id),
           'name': position.name,
           'foreign_key': foreign_key,
           'tags': tags,
           'info': info,
           'parent_id': position.parent_id}
    return ret


def get_position_info(position_id):
    position = PositionDesc.objects(id=position_id,
                                    soft_del=False).first()
    if not position:
        return None
    info = position_to_dict(position)
    if position.path:
        root_position = PositionDesc.objects(id=position.path[0],
                                             soft_del=False).first()
        if root_position:
            info['root_name'] = root_position.name
    return info


def get_sub_positions(position_ids, included=False):
    '''
    获取某些职位(id)的全部下级职位。
    Params
    ------
    - position_ids: 职位id列表
    - included: boolean, default False, 是否包含position_ids中的职位
    '''
    query = Q(soft_del=False)
    if included:
        query = query & (Q(id__in=position_ids) | Q(path__in=position_ids))
    else:
        query = query & Q(path__in=position_ids)
    positions = list(PositionDesc.objects(query))
    positions = sorted(positions, key=lambda x: chinese_num_replace(x.name))
    return positions


def get_granted_position_ids(user_id, include_roles=True):
    '''
    get_granted_position_ids(user_id, include_roles=True)
    获取授权给用户的position_id列表，这个列表是未经扩展过的
    '''
    position_ids = set()
    user_perm = UserPerm.objects(user_id=user_id, soft_del=False).first()
    if not user_perm:
        pass
    else:
        position_ids |= set(user_perm.granted_positions)
        if include_roles and user_perm.roles:
            roles = RoleDesc.objects(id__in=user_perm.roles,
                                     soft_del=False)
            for role in roles:
                position_ids |= set(role.granted_positions)
    return position_ids


def get_all_granted_position_ids(user_id):
    position_ids = get_granted_position_ids(user_id)
    sub_positions = get_sub_positions(position_ids, included=True)
    return [str(i.id) for i in sub_positions]


def get_users_by_positions(position_ids,
                           include_deleted_users=False):
    user_perms = UserPerm.objects(position_id__in=position_ids, soft_del=False)
    user_ids = map(lambda x: x.user_id, user_perms)
    filters = {'id__in': user_ids}
    if not include_deleted_users:
        filters['soft_del'] = False
    users = User.objects(**filters)
    return list(users)


def get_users_by_sub_positions(position_ids,
                               included=True,
                               include_deleted_users=False):
    sub_position_ids = map(lambda x: str(x.id),
                           get_sub_positions(position_ids,
                                             included=included))
    return get_users_by_positions(sub_position_ids,
                                  include_deleted_users=include_deleted_users)


def get_all_sub_users(user_id):
    position_ids = get_granted_position_ids(user_id)
    sub_positions = get_sub_positions(position_ids, included=True)
    users = []
    if not sub_positions:
        pass
    else:
        users = get_users_by_positions(position_ids)
    user_perm = UserPerm.objects(soft_del=False, user_id=user_id).first()
    if user_perm and user_perm.position_id:
        user = User.objects(id=user_id).first()
        if user:
            users.append(user)
    return users


def is_upstream_position(curr_user, position_id=None, user_id=None, position_ids=None):
    curr_user = curr_user if hasattr(curr_user, 'id')\
                else User.objects(id=curr_user).first()
    if position_ids:
        pass
    elif user_id and not position_id:
        user_perm = UserPerm.objects(user_id=user_id, soft_del=False).first()
        if user_perm and user_perm.position_id:
            position_id = user_perm.position_id
            position_ids = [position_id]
    elif position_id:
        position_ids = [position_id]

    if not position_ids:
        return False
    position_ids = [i for i in position_ids if i]
    curr_position_ids = get_granted_position_ids(str(curr_user.id))
    if curr_position_ids:
        positions = {str(p.id): p for p in\
                     PositionDesc.objects(id__in=position_ids, soft_del=False)}
        if len(positions) != len(position_ids):
            return False
        for position_id, position in positions.items():
            if not any([i in position.path or i == position_id\
                        for i in curr_position_ids]):
                return False
        else:
            return True
    return False


def is_owner(curr_user, position_id=None, user_id=None):
    curr_user = curr_user if hasattr(curr_user, 'id')\
                else User.objects(id=curr_user).first()
    if user_id and str(curr_user.id) == user_id:
        return True
    #if not position_id:
    #    return False
    #curr_user_perm = UserPerm.objects(user_id=str(curr_user.id), soft_del=False).first()
    #if curr_user_perm and curr_user_perm.position_id == position_id:
    #    return True
    return False


def set_position(user_id, position_id):
    '''
    设置用户的职位，当position is None时，用户的职位为空。
    '''
    with cache_lock("user_%s" % user_id):
        position = None
        user_perm = user_perm_ops.get_or_create_user_perm(user_id)
        user = User.objects(id=user_id, soft_del=False).first()
        if not (user_perm and user):
            return False, "用户不存在或已删除"
        position_id = position_id or ''
        if position_id:
            position = PositionDesc.objects(id=position_id,
                                            soft_del=False).first()
            if not position:
                return False, "职位不存在"
        user_perm.position_id = position_id
        user_perm.save()
        user.info['position_id'] = position_id
        user.info['position_name'] = position.name if position else ""
        user.info['position_tags'] = position.tags if position else []
        user.info['position_path'] = position.path if position else []
        user.save()
        return True, user_perm


def set_granted_positions(user_id, position_ids):
    user = User.objects(id=user_id, soft_del=False).first()
    if not user:
        return False, "用户不存在或已删除"
    user_perm = user_perm_ops.get_or_create_user_perm(user_id)
    positions = PositionDesc.objects(soft_del=False, id__in=position_ids)
    position_ids = list(map(lambda x: str(x.id), positions))
    user_perm.granted_positions = position_ids
    user_perm.save()
    return True, user_perm


def grant_position(op, position_id, user_id=None, role_id=None):
    if not user_id and not role_id:
        return False, "未提供user_id或者role_id"
    position = PositionDesc.objects(soft_del=False, id=position_id).first()
    if not position:
        return False, "职位或团队id未提供"
    perm_obj = None
    if user_id:
        perm_obj = user_perm_ops.get_or_create_user_perm(user_id)
    elif role_id:
        perm_obj = RoleDesc.objects(soft_del=False, id=role_id).first()
    if not perm_obj:
        return False, "目标用户或者角色不存在"
    if op == 'add':
        perm_obj.granted_positions = list(set(perm_obj.granted_positions) | set([position_id]))
    elif op == 'del':
        perm_obj.granted_positions = list(filter(lambda x: x != position_id, perm_obj.granted_positions))
    else:
        raise Exception("Unknown exception names.")
    perm_obj.save()
    return True, perm_obj.granted_positions


def position_id_by_name(name):
    position = PositionDesc.objects(soft_del=False, name=name).first()
    return str(position.id)


def position_ids_by_names(names):
    positions = PositionDesc.objects(soft_del=False, name__in=names)
    return list(map(lambda x: str(x.id), positions))


def get_position_by_foreign_key(foreign_key):
    if not foreign_key:
        return None
    position = PositionDesc.objects(foreign_key=foreign_key,
                                    soft_del=False).first()
    return position


def add_position(name,
                 parent_id=None,
                 parent_name=None,
                 foreign_key=None,
                 allow_duplicate=False):
    cache_key = "position"
    if parent_name and not parent_id and not allow_duplicate:
        parent_position = PositionDesc.objects(soft_del=False,
                                               name=parent_name).first()
        if parent_position:
            parent_id = str(parent_position.id)
    with cache_lock(cache_key):
        position = get_position_by_foreign_key(foreign_key)
        if position:
            return False, "外键已经存在"
        position = PositionDesc.objects(soft_del=False, name=name).first()
        if allow_duplicate is not True and position:
            return False, "职位或团队名称重复"
        parent = None
        if parent_id:
            parent = PositionDesc.objects(soft_del=False, id=parent_id).first()
            if not parent:
                return False, "职位或团队的上级职位不存在"
        position = PositionDesc(name=name,
                                parent_id=parent_id,
                                foreign_key=foreign_key)
        if parent:
            position.path = parent.path + [parent_id]
        position.save()
        return True, position


def remove_position(position_id, allow_recursive=False):
    cache_key = "position"
    with cache_lock(cache_key):
        if not allow_recursive and\
                PositionDesc.objects(soft_del=False, parent_id=position_id):
            return False, "目标职位或团队尚有下级存在"
        if allow_recursive:
            for i in PositionDesc.objects(soft_del=False, path=position_id):
                i.soft_del = True
                i.save()
        position = PositionDesc.objects(id=position_id).first()
        if position and not position.soft_del:
            position.soft_del = True
            position.save()
        return True, position


def move_position(position_id, target_parent_id=''):
    cache_key = "position"
    with cache_lock(cache_key):
        position = PositionDesc.objects(soft_del=False, id=position_id).first()
        if not position:
            return False, "职位或团队不存在"
        target_parent = None
        if target_parent_id:
            target_parent = PositionDesc.objects(soft_del=False,
                                                 id=target_parent_id).first()
            if not target_parent:
                return False, "上级职位或团队不存在"
            if str(position.id) in target_parent.path:
                return False, "上级职位是当前职位的下级"
            if position_id == target_parent_id:
                return False, "上级职位于当前职位相同"
        position.parent_id = target_parent_id
        if target_parent:
            position.path = target_parent.path + [target_parent_id]
        else:
            position.path = []
        position.save()
        for i in PositionDesc.objects(soft_del=False, path=position_id):
            pos = i.path.index(position_id)
            i.path = position.path + i.path[pos:]
            i.save()
        return True, position


def rename_position(position_id, new_name, allow_duplicate=False):
    cache_key = "position"
    with cache_lock(cache_key):
        if not allow_duplicate and PositionDesc.objects(soft_del=False,
                                                        name=new_name).first():
            return False, "相同名称的职位或者团队已经存在"
        position = PositionDesc.objects(soft_del=False, id=position_id).first()
        if not position:
            return False, "职位或者团队不存在"
        position.name = new_name
        position.save()
        return True, position


def position_tree(position_ids, extend_users=False):
    '''
    获取职位的树形结构
    '''
    def convert(obj):
        return {'label': obj.name,
                'value': str(obj.id),
                'children': []}
    positions = get_sub_positions(position_ids, included=True)
    all_ids = set(map(lambda x: str(x.id), positions))

    users_dict = {}
    if extend_users:
        user_perm_list = list(UserPerm.objects(soft_del=False, position_id__in=all_ids))
        users = {str(u.id): {'label': u.name, 'value': 'user %s' % str(u.id)}\
                     for u in User.objects(soft_del=False,
                     id__in=list(map(lambda x: x.user_id, user_perm_list)))}
        for up in user_perm_list:
            users_dict.setdefault(up.position_id, [])
            user = users.get(up.user_id)
            if user:
                users_dict[up.position_id].append(user)

    head_positions = filter(lambda x: x.parent_id not in all_ids,
                            positions)
    stack = deque()
    stack.extend(list(map(convert, head_positions)))
    ret = [i for i in stack]
    while stack:
        curr = stack.popleft()
        subs = list(map(convert,
                        filter(lambda x: x.parent_id == curr['value'],
                               positions)))
        curr['children'] = []
        curr['children'].extend(subs)
        if extend_users:
            curr['children'].extend(users_dict.get(curr['value']) or [])
        if not curr['children']:
            del curr['children']
        else:
            curr['children'] = [{'label': '全部', 'value': curr['value']}]\
                               + curr['children']
        stack.extendleft(subs)
    return ret


def position_tree_dump():
    ret = []
    positions = list(PositionDesc.objects(soft_del=False))
    stack = deque()
    stack.extend(list(filter(lambda x: not x.parent_id, positions)))
    while stack:
        curr = stack.popleft()
        subs = (list(filter(lambda x: x.parent_id == str(curr.id),
                            positions)))
        stack.extendleft(subs)
        output = "%s %s %s %s" % ("    " * len(curr.path or []), "+" if subs else "-", curr.name, str(curr.id))
        ret.append(output)
    return '\n'.join(ret)


def fix_path():
    positions = list(PositionDesc.objects(soft_del=False))
    stack = deque()
    stack.extend(list(filter(lambda x: not x.parent_id, positions)))
    while stack:
        curr = stack.popleft()
        if not curr.parent_id:
            curr.path = []
        else:
            parent = PositionDesc.objects(id=curr.parent_id).first()
            curr.path = parent.path + [curr.parent_id]
        curr.save()
        subs = (list(filter(lambda x: x.parent_id == str(curr.id),
                            positions)))
        stack.extendleft(subs)


def get_position_leaders(position_id):
    user_perms = UserPerm.objects(position_id=position_id,
                                  granted_positions=position_id)
    user_ids = [up.user_id for up in user_perms]
    return user_ids
