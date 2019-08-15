# pauli -- Permission, Auth, User Library and Interface

A library for managing permission, authentication and users, can be used as a plugin(via blueprint) into flask projects.

## Permission description

A permission description is list of permission objects. A permission object is like

```
{
    "action": "gesafe:article:*",
    "effect": "allow",
    "resource": ["*"] 
}
```

Where 

- action: the action of the permission, like editing article, delete products.
- effect: optional, default "allow", can be either "allow" or "deny".
- resource: optional, default "*", the target where action take upon.
    - "*": everything
    - "+": everything adapt the user's organization.
    - "-": restricted to the content created by the user.
    - "<DOMAIN>:<APP>:<RESOURCE>": specified resources.
