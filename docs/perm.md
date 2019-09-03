# perm模块API

## GET /pauli/perm/api/perm/list
必须登录，获取当前用户或者指定用户的全部权限
如果为指定用户，那么当前用户必须有 pauli:perm:user:get 权限

__Params__
- user\_id: str, optional, 指定用户的用户id
- exclude\_role: str, 此参数为'1'时，只返回用户自己的权限，不包括用户所在的角色中的权限

__Result__
- perm\_list: list, 用户的权限列表
- user\_id: str, 被查询用户的用户id


## POST /pauli/perm/api/perm/has
必须登录，检查当前用户或者指定用户是否有某一个项权限

__Params__
- perm: object or str, 权限描述，比如"gesafe:*", 或者{"action": "gesafe:*", "effect": "allow", "resource": "*"}
- user\_id: str, optional, 指定的用户id，如果不传则默认为对当前用户进行查询，如果传此参数，需要pauli:perm:user:get权限

__Result__
- has: boolean, 是否拥有当前权限


## POST /pauli/perm/api/perms/has
必须登录，检查当前用户或者指定用户是否拥有一个系列的权限（权限的描述仅可使用字符串方式描述）

__Params__
- perms: list of str, 权限描述列表
- return\_type: str, default 'dict', 返回的列表形式，可以为'list'或者'dict'
- user\_id: str, optional, 指定的用户id，如果不传则默认为对当前用户进行查询，如果传此参数，需要pauli:perm:user:get权限

__Result__
- perms: list or dict, 用户是否拥有某些权限的列表


## GET /pauli/perm/api/perm/triple
必须登录，检查当前用户是否具有同一的action的'*', '+', '-'三种resource的权限

__Params__
- action: str, required, perm的action

__Return__
- result
    - triple
        - '*': 如果无此权限为False，否则为True
        - '+': 如果无此权限为False，否则为用户被授权过得全部position\_id的list
        - '-': 如果无此权限为False，否则为用户的user_id


## POST /pauli/perm/api/perm/triples
必须登录，检查当前用户是否具有actions中每一个action的'*', '+', '-'三种resource的权限

__Params__
- actions: list of str, required

__Return__
- result
    - triples: dict，每个项目的key为action本身，value为如下的dict 
        - '*': 如果无此权限为False，否则为True
        - '+': 如果无此权限为False，否则为用户被授权过得全部position\_id的list
        - '-': 如果无此权限为False，否则为用户的user_id


## PUT /pauli/perm/api/perm/user/add
必须登录，为用户增加权限，访问用户必须有 pauli:perm:user:update 权限

__Params__
- perm: object or str, 权限描述
- user\_id: str, 要被赋予权限的用户

__Result__
- perm\_list: object, 当前用户的权限列表


## PUT /pauli/perm/api/perm/user/del
必须登录，为用户删除权限，访问用户必须有 pauli:perm:user:update 权限

__Params__
- perm: object or str, 权限描述
- user\_id: str, 要被删除权限的用户

__Result__
- perm\_list: object, 当前用户的权限列表


## PUT /pauli/perm/api/perm/user/update
更新一个用户自己的全部权限(即在GET /pauli/perm/api/perm/list API中，以exclude\_role=='1'的形式获取的权限）。

__Params__

- perms: list, 权限列表
- user\_id: str, 用户的id

__Returns__

- result:
    - perm\_list: list，用户的权限列表


## GET /pauli/perm/api/role/list
必须登录，要求pauli:perm:role权限，获取全部的角色列表

__Result__
- roles: list, 角色列表


## GET /pauli/perm/api/role/user/list
必须登录，获取用户的角色列表，查询自己的不需要额外权限，查询其他人则需要pauli:perm:user:get权限

__Params__
- user\_id: str, optional, 如果查询其他人时，需要提供的对应用户的user\_id
 
__Result__
- roles: list, 角色列表


## PUT /pauli/perm/api/role/user/update
更新用户的角色id列表，需要pauli:perm:user:update权限

__Params__
- user\_id: str, 用户id
- role\_ids: list of str, 用户角色id列表

__Result__
- result:
    - roles: list of role obj, 更新后用户的列表，同 GET /pauli/perm/api/role/user/list的返回结果


## PUT /pauli/perm/api/perm/role/add
必须登录，为角色增加权限，访问用户必须有 pauli:perm:role:update 权限

__Params__
- perm: object or str, 权限描述
- role\_id: str, 要被赋予权限的角色

__Result__
- perm\_list: object, 角色的权限列表


## GET /pauli/perm/api/role
必须登录，获取某一角色的信息，访问用户必须有 pauli:perm:role:get 权限

__Params__
- role\_id: str, 角色id

__Result__
- role: object, 角色的描述


## PUT /pauli/perm/api/perm/role/del
必须登录，为角色删除权限，访问用户必须有 pauli:perm:role:update 权限

__Params__
- perm: object or str, 权限描述
- role\_id: str, 要被删除权限的角色

__Result__
- perm\_list: object, 角色的权限列表


## PUT /pauli/perm/api/role/user
必须登录，分配给用户角色，访问用户必须有 pauli:perm:user:update 权限

__Params__
- role\_id: str, 角色id
- user\_id: str, 用户id

__Result__
- roles: list, 用户的角色列表


## DELETE /pauli/perm/api/role/user
必须登录，解除给用户的角色，访问用户必须有 pauli:perm:user:update 权限

__Params__
DELETE方法在url中传递参数
- role\_id: str, 角色id
- user\_id: str, 用户id

__Result__
- roles: str, 用户的角色列表


## POST /pauli/perm/api/role
必须登录，需要 pauli:perm:role:create 权限，创建一个新的角色

__Params__
- name: str，角色名

__Result__
- role: object, 角色信息


## DELETE /pauli/perm/api/role
必须登录，需要 pauli:perm:role:del 权限，删除一个现有角色

__Params__
- role\_id: object, 角色id

__Result__
- role: object, 角色信息，soft\_del会被设置为true


## PUT /pauli/perm/api/role
必须登录，需要 pauli:perm:role:update 权限，更新一个现有角色信息

__Params__
- role\_id: object, 角色id
- name: str, 角色名

__Result__
- role: object, 角色信息