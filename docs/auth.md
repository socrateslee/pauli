# auth模块

## GET /pauli/auth/api/logined
application/json，判断用户是否登录

__Returns__

- code: int, 0表示用户
- result:
    - logined: boolean, 用户是否登录
    登录状态下，还会包括
    - user\_id: str, 用户id
    - name: str, 用户的名字
    - email: str, 可能为空，用户邮件地址
    - mobile: str, 可能为空，用户的手机
    - position\_id: str, 可能为空，用户的职位或者团队id


## GET /pauli/auth/api/record
获取用户的登陆就记录，需要pauli:user:audit权限

__Params__
- user\_id: str, 用户id
- cursor\_id: str, 用于分页cursor\_id，即请求此cursor\_id之后id
- limit: int，default 10, 返回结果数量

__Returns__
- result:
    - logs: 登录记录
        - record\_id: 记录id
        - login\_type: 登录类型
        - user\_id: 用户id
        - time: 登录时间


## POST /pauli/auth/api/pass/create
application/json，创建一个通过用户名密码登录的用户，需要pauli:user:create权限

__Params__

- username: str, required, 用户名（电子邮件地址）
- password: str, optional, 初始密码，如果不提供会随机设定一个密码
- name: str, required, 用户的名字
- mobile: str, optional, 用户的初始手机号


## PUT /pauli/auth/api/pass/login
application/json，通过用户名密码登录

__Params__
- username: string, 用户名
- password: string, 密码

__Returns__
- code: int,
    - 0, E_SUCC, 表示登陆成功
    - 1032, sc.E_USER_NEED_SMS_AUTH, 表示用户名密码正确，但是需要通过确认码验证手机（验证码已经发送过）


## GET /pauli/auth/api/pass/code
请求发送手机验证码（语音/短信验证码），但是必须已经在二十分钟内通过PUT /pauli/auth/api/pass/login api 成功的验证过用户名和密码。

__Params__
- method: str, "voice"或者"sms"，默认值为"voice"

__Returns__
- code: int
    - 0, E_SUCC, 表示发送成功
    - 其他为错误

## POST /pauli/auth/api/pass/code
通过手机验证码登录，必须是在二十分钟内容过PUT /pauli/auth/api/pass/login api成功验证过用户名密码

__Params__
- code: str, 用户输入的手机验证码

__Returns__
- code: 0, 登录成功，其他为不成功


## GET /pauli/auth/api/logout
登出用户

__Returns__
- code: int, 0表示登出成功


## GET /pauli/auth/api/pass/reset
获取重置登录凭证邮件，成功的请求将向用户发送一封包含重置code的邮件

__Params__
- email: str, required, 用户邮件地址 

__Returns__
- code: int, 0表示获取成功，其他均为不成功


## PUT /pauli/auth/api/pass/reset
验证重置登录凭证的code的是否有效，仅用于提示用户code是否正确，多次访问后code会失效

__Params__
- code: str, required, 重置登录凭证

__Returns__
- code: int, 0表示有效，其他为无效


## POST /pauli/auth/api/pass/reset
重置登录凭证

__Params__
- code: str, required, 登录凭证的code，从邮件中获取
- password: str, optional，新密码
- mobile: str, optional，新的手机号码

__Returns__
- code: int, 0为成功，其余失败

