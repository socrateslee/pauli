import re
import six

ACTION_PATTERN = re.compile(r"^[_a-zA-Z0-9-]+$")


def is_valid_action(action_str):
    '''
    Check whether an action_str is valid.
    Valid action examples:
        "gesafe:storage:*"
        "tianfu:article:write"
    '''
    segment_list = action_str.strip().split(":")
    if not segment_list:
        return False
    for segment in segment_list[:-1]:
        if not (ACTION_PATTERN.match(segment) or segment == '*'):
            return False
    if (not ACTION_PATTERN.match(segment_list[-1])) and segment_list[-1] != '*':
        return False
    return True


def is_valid_resource(resource_str):
    '''
    Check whether an resource_str is a valid resource description.
    Valid resource examples
        "gesafe:article:*"
        "gesafe:article:+"
        "gesafe:article:-"
        "tianfu:article:write"
    '''
    segment_list = resource_str.strip().split(":")
    if not segment_list:
        return False
    for segment in segment_list[:-1]:
        if not ACTION_PATTERN.match(segment):
            return False
    if (not ACTION_PATTERN.match(segment_list[-1]))\
            and segment_list[-1] not in ['*', '+', '-']:
        return False
    return True


def is_action_matched(user_action, target_action):
    '''
    Check whether an action provided as user_action can match
    a target_action.
    '''
    if not is_valid_action(user_action):
        return False
    user_list = user_action.strip().split(":")
    target_list = target_action.strip().split(":")
    for idx, segment in enumerate(user_list):
        if idx >= len(target_list):
            return False
        elif user_list[idx] != "*" and user_list[idx] != target_list[idx]:
            return False
    if len(user_list) < len(target_list) and\
             user_list and user_list[-1] != '*':
        return False
    return True


def is_resource_matched(user_resource, target_resource,
                        is_upstream=False, is_owner=False):
    if not is_valid_resource(user_resource):
        return False
    user_list = user_resource.strip().split(":")
    target_list = target_resource.strip().split(":")
    for idx, segment in enumerate(user_list):
        if idx >= len(target_list):
            return False
        elif user_list[idx] == "*":
            continue
        elif user_list[idx] == '+'\
                and target_list[idx] != '*' and is_upstream:
            continue
        elif user_list[idx] in ('+', '-') and is_owner:
            continue
        elif target_list[idx] in ('+', '-'):
            return False
        elif user_list[idx] != target_list[idx]:
            return False
    return True


def is_resources_matched(user_resources, target_resource,
                         is_upstream=False, is_owner=False):
    for ur in user_resources:
        if is_resource_matched(ur, target_resource,
                               is_upstream=is_upstream,
                               is_owner=is_owner):
            return True
    return False


def get_perm_desc_from_string(string_desc):
    return {'action': string_desc,
            'effect': 'allow',
            'resource': '*'}


def is_perm_matched(user_perm_desc, target_perm_desc,
                    is_upstream=False, is_owner=False,
                    ignore_effect=False):
    return is_action_matched(user_perm_desc['action'],
                             target_perm_desc['action'])\
           and (user_perm_desc['effect'] == target_perm_desc['effect']
                if not ignore_effect else True)\
           and is_resource_matched(user_perm_desc['resource'],
                                    target_perm_desc['resource'],
                                    is_upstream=is_upstream,
                                    is_owner=is_owner)


def is_perm_allowed(user_perm_desc_list, target_perm_desc,
                    is_upstream=False, is_owner=False):
    if isinstance(user_perm_desc_list, dict):
        user_perm_desc_list = [user_perm_desc_list]
    allowed = False
    for perm_desc in user_perm_desc_list:
        is_matched = is_perm_matched(perm_desc, target_perm_desc,
                                     is_upstream=is_upstream, is_owner=is_owner,
                                     ignore_effect=True)
        if not is_matched:
            continue
        if perm_desc['effect'] == 'deny':
            allowed = False
            break
        else:
            allowed = True
    return allowed


def is_valid_perm_desc(perm):
    if isinstance(perm, six.string_types):
        perm = get_perm_desc_from_string(perm)
    action = perm.get('action')
    effect = perm.get('effect')
    resource = perm.get('resource')
    return action and is_valid_action(action)\
           and effect and effect.lower() in ['allow', 'deny']\
           and resource and is_valid_resource(resource)


def equ(perm1, perm2):
    return perm1['action'] == perm2['action']\
           and perm1['effect'] == perm2['effect']\
           and perm1['resource'] == perm2['resource']
