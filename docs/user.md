# user模块

## user json 对象

一些必要的字段在user的json对象中的含义：

- user\_id: str，用户的id
- created：str，用户的创建时间
- name: str，用户的名字，注意这不是唯一的
- soft\_del: boolean，用户是否处于软删除状态
- email：str，用户的的电子邮件地址，对于使用用户名密码登录的用户，这个字段就是用户名
- mobile：str，用户的手机号码，可能为空
- position\_id: str，用户的职位id，可能为空
- position\_name: str，用户的位置名称，可能为空
- creator\_id: str，用户的创建者id，可能为空
- creator\_name: str，用户的创建者的名字，可能为空


## GET /pauli/user/api/list
application/json，获取全部用户列表，需要pauli:user:list权限

__Params__

- keyword: str, optional, 查询关键词
- enabled: str, optional, '1'为显示有效用户，'0'为无效用户，不传次参数时，显示全部用户

__Returns__

- code: int, 0表示用户
- result:
    - user_list: obj, 用户信息列表

## POST /pauli/user/api/info
application/json，获取用户名dict

__Params__
- user\_ids: list, required, 用户id的列表

__Returns__
- code: int, 0表示登陆成功
- result
    - info: dict, user\_id: inf_object 的key-value对，如果列表中的用户不存在，不会返回在结果中。info\_object的结构包括：name, position_id, position_name, email。


## GET /pauli/user/api/query/byinfo
根据mobile或者email获取用户的信息

__Params__
- query\_type: str, required, 查询类型，可以为mobile, email或者role\_name
- query\_value: str, required, 查询的值

__Returns__
- code: int, 0表示登录成功
- result:
    - users: 用户的info对象列表


## GET /pauli/user/api/get/byinfo
根据mobile, email或者role\_name获取用户的信息

__Params__
- query\_type: str, required, 查询类型，可以为mobile或者email
- query\_value: str, required, 查询的值

__Returns__
- code: int, 0表示登录成功
- result:
    - user: 用户的info对象，如果用户不存在则为None


## POST /pauli/user/api/names
application/json，获取用户名dict

__Params__
- user\_ids: list, required, 用户id的列表

__Returns__
- code: int, 0表示登陆成功
- result
    - user_names: dict, user\_id: name 的key-value对，如果列表中的用户不存在，不会返回在结果中


## GET /pauli/user/api/query
applicaiton/json，获取用户，需要pauli:user:upate权限 

__Params__
- keyword: 用户名或者用户姓名

__Returns__
- code: int, 0表示登出成功
- result
    - user_list: list of obj, 用户信息列表


## GET /pauli/user/api/enabled
使用户有效

__Params__
- user\_id: 用户id

__Returns__
- code: int, 0表示成功
- result
    - user: 用户信息obj


## DELETE /pauli/user/api/enabled
停用用户

__Params__
- user\_id: 用户id

__Returns__
- code: int, 0表示成功
- result
    - user: 用户信息obj


## PUT /pauli/user/api/info/update
更新用户信息

__Params__
- user\_id: str, 用户id
- name: str, 用户的名字

__Returns__
- code: int, 0表示成功
- result:
    - user: 用户信息obj

## GET /pauli/user/api/audit
获取用户的相关信息audit log

__Params__
- user\_id: str, 用户id
- cursor\_id: str, 用于分页cursor\_id，即请求此cursor\_id之后id
- limit: int，default 10, 返回结果数量

__Returns__
- result:
    - logs: audit log
        - log\_id: 日志id
	- created: 发生时间
	- user\_id: 用户id
	- editor\_id: 编辑人用户id
	- editor\_name: 编辑人姓名
	- msg: 发生的信息的描述
	