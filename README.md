# pauli -- Permission, Auth, User Library and Interface

A library for managing permission, authentication and users, can be used as a plugin(via blueprint) into flask projects.

## Permission description

A permission description is list of permission objects. A permission object is like

```
# Allow every permissions on system:article
{
    "action": "system:article:*",
    "effect": "allow",
    "resource": "*"
}

# Deny every permissions on system:crm for departments managed by the underlyting user
{
    "action": "system:article:*",
    "effect": "deny",
    "resource": "+"
}
```


Where 

- action: the action of the permission, like editing article, delete products.
- effect: optional, default "allow", can be either "allow" or "deny".
- resource: optional, default "*", the target where action take upon.
    - "*": everything
    - "+": everything within the user's organization.
    - "-": restricted to the content created by the user.
    - "<DOMAIN>:<APP>:<RESOURCE>": specified resources.


## How to integrate pauli to your project

pauli is designed as a blueprint in a flask project. To integrate pauli, consider

- pauli use mongodb as its backend
- Wrap pauli into a your project, and deploy as a service.
