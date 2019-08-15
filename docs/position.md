# perm模块的职位和团队API

## GET /pauli/perm/api/position/dump
需要pauli:perm:position:dump权限，返回全部职位和团队的tree结构。注意只能返回团队本身的树结构，或许指定的团队的成员时，需要使用 API GET /pauli/perm/api/position/users

__Returns__

- result:
    - dump: str, 职位和团队的结构


## GET /pauli/perm/api/position/tree
需要登录，返回当前用户被授权过的职位树

__Params__
- extend: str, optional, 默认不需要提供，当extend=1时，返回结果中会把用户也attach到职位树的叶子节点上
- position\_id: str, optional, 默认不需要提供，如果提供，则返回指定position\_id以下（含）的职位树。传此参数时，需要 pauli:perm:position:list 权限

__Returns__

- result:
    - tree: 职位树结构，每个树节点的结构为
        - label: 职位或者团队名称
        - value: 默认为职位id，如果为用户时，结构为"user <user_id>"
        - children: list, 下一级节点


## GET or POST /pauli/perm/api/position/users
需要登录，获取某个指定职位或者团队的全部users列表
如果用户的被授权的职位范围涵盖了请求的position\_id，才能返回正常的结果

__Params__
- position\_id: str, optional, __仅在GET方法是使用__，职位或者团队id，
                提供此参数时，返回的是指定的position下的用户列表
                不提供此参数及position_ids时，返回时的用户被授权的全部职位或团队下的用户列表
- position\_ids: list, optional, __仅在POST方法时使用__，职位或者团队id列表，
                提供此参数时，返回的是指定的position_ids下的用户列表
                不提供此参数及position_id时，返回时的用户被授权的全部职位或团队下的用户列表

__Returns__

- result:
    - users: 用户的列表


## GET/POST /pauli/perm/api/position/list
获取某一个或多个position下属的，或者自己下属的团队/职位列表。如果传递position\_id或者position\_ids，那么需要 pauli:perm:position:list 权限。

__Params__

- position\_id: str, 仅在GET时有效，可选，目标的position_id
- position\_ids: list of str, 尽在POST时有效，可选，目标的position\_id列表

__Returns__

- result
    - position_list: list or str, position的id列表，id列表中包含请求的position_id，包含请求的position的非直接子节点的position_id


## GET /pauli/perm/api/position
无需特殊权限，获取一个职位的信息

__Params__
- position\_id: 职位的id

__Returns__
- result:
    - position: str, 职位或者团队描述 
        - id: 职位或者团队id
        - name: 职位或者团队名字
        - parent\_id: 职位或者团队的父级position的id
        - root_name: optional, 职位的祖先职位的名字


## PUT /pauli/perm/api/positions
无需特殊权限，获取一个列表的职位的信息

__Params__
- position\_ids: 职位的id列表

__Returns__
- result:
    - positions: dict, positions的dict，key为position\_id，value为如下结构
        - id: 职位或者团队id
        - name: 职位或者团队名字
        - parent\_id: 职位或者团队的父级position的id
        - root_name: optional, 职位的祖先职位的名字


## POST /pauli/perm/api/position
需要pauli:perm:position:add权限，增加一个职位或者团队描述

__Params__
- name: str, required, 职位名称，在系统内不可重复
- parent_id: str, optional, 父级职位或者团队的id
- parent_name: str, optional, 父级职位或者团队的名称

注意，如果parent_id和parent_name都没有提供，那么认为这个职位或者团队没有父级。

__Returns__
- result
    - position: str, 职位或者团队描述 
        - id: 职位或者团队id
        - name: 职位或者团队名字
        - parent\_id: 职位或者团队的父级position的id


## DELETE /pauli/perm/api/position
删除职位或者团队，需要pauli:perm:position:delete权限

__Params__
- position\_id: str, required, 职位或者团队的id

__Returns__
- result
    - position: str, 被删除的职位或者团队描述
        - id: 职位或者团队id
        - name: 职位或者团队名字
        - parent\_id: 职位或者团队的父级position的id


## PUT /pauli/perm/api/position
需要pauli:perm:position:update权限，更改职位或者团队的信息，包括

- 更改名字
- 更改父级职位或团队

__Params__
- position\_id: str, required, 职位或者团队的id
- parent\_id: str, optional, 父级职位或者团队id，如果提供此参数但是内容字符创的话，表示更改为没有父级团队
- new\_name: str, optional, 要更改为的新的名字

__Returns__
- result
    - position: str, 被删除的职位或者团队描述
        - id: 职位或者团队id
        - name: 职位或者团队名字
        - parent\_id: 职位或者团队的父级position的id


## POST /pauli/perm/api/perm/user/position
需要pauli:perm:user:update权限，设置用户属于的职位或者团队，一个用户只能属于一个职位或者团队

__Params__
- user\_id: 用户id
- position\_id: 职位或者团队id

__Returns__
- position\_id: 用户的职位或者团队id


## GET /pauli/perm/api/perm/user/position
获取用户被直接赋予的职位id列表，不包含角色中的职位id，也不扩展职位的下级职位。如果查询的不是用户自己需要pauli:perm:user:get 权限

__Params__
- user\_id: str, optional, 用户id，不传则使用当前用户的id

__Returns__
- result
    - positions: list of str, 被直接授权的职位id列表


## PUT /pauli/perm/api/perm/user/position/grant
需要pauli:perm:user:update权限，把某个团队的权限授权给一个用户（比如这个用户是团队长或者客服）

__Params__
- user\_id: 用户的id
- position\_id: 职位或者团队id

__Returns__
- result
    - grant\_positions: 已经授权该用户的全部团队或者职位列表


## PUT /pauli/perm/api/perm/user/position/recall
需要pauli:perm:user:update权限，撤销对用户的某个团队的权限授权（比如这个用户是团队长或者客服）

__Params__
- user\_id: 用户的id
- position\_id: 职位或者团队id

__Returns__
- result
    - grant\_positions: 已经授权该用户的全部团队或者职位列表


## PUT /pauli/perm/api/perm/role/position/grant
需要pauli:perm:role:update权限，把某个团队的权限授权给一个角色

__Params__
- role\_id: 角色的id
- position\_id: 职位或者团队id

__Returns__
- result
    - grant\_positions: 已经授权该角色的全部团队或者职位列表


## PUT /pauli/perm/api/perm/role/position/recall
需要pauli:perm:role:update权限，撤销对角色的某个团队的权限授权

__Params__
- role\_id: 角色的id
- position\_id: 职位或者团队id

__Returns__
- result
    - grant\_positions: 已经授权该局角色的全部团队或者职位列表


## PUT /pauli/perm/api/perm/user/position/update
需要 pauli:perm:role:update权限，整体更新用户被授权的团队id列表

__Params__
- user\_id: 用户id
- position\_ids: 授权的团队的id列表

__Returns__
- result
    - grant_positions: 用户的全部被授权的position_ids