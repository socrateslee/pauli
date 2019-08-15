from ..perm.ops import perm_base as perm_base


ADMIN_PERM = {
    "action": "*",
    "effect": "allow",
    "resource": "*"
}

TEST_ALLOW_PERM_STAR = {
    "action": "test:*",
    "effect": "allow",
    "resource": "*"
}

TEST_ALLOW_PERM_STAR_MIDDLE = {
    "action": "test:*:foo",
    "effect": "allow",
    "resource": "*"
}

TEST_ALLOW_PERM = {
    "action": "test:foo:bar",
    "effect": "allow",
    "resource": "*"
}

TEST_ALLOW_PERM_PLUS = {
    "action": "test:*",
    "effect": "allow",
    "resource": "+"
}

TEST_ALLOW_PERM_MINUS = {
    "action": "test:*",
    "effect": "allow",
    "resource": "-"
}

TEST_DENY_PERM_STAR = {
    "action": "test:*",
    "effect": "deny",
    "resource": "*"
}

def test_is_valid_perm_desc():
    assert perm_base.is_valid_perm_desc(ADMIN_PERM)
    assert perm_base.is_valid_perm_desc(TEST_ALLOW_PERM_STAR)
    assert perm_base.is_valid_perm_desc(TEST_ALLOW_PERM_STAR_MIDDLE)
    assert perm_base.is_valid_perm_desc(TEST_ALLOW_PERM_PLUS)
    assert perm_base.is_valid_perm_desc(TEST_ALLOW_PERM_MINUS)
    assert perm_base.is_valid_perm_desc(TEST_DENY_PERM_STAR)


def test_is_resource_matched():
    assert perm_base.is_resource_matched("*", "*")
    assert perm_base.is_resource_matched("*", "+")
    assert perm_base.is_resource_matched("*", "-")
    assert perm_base.is_resource_matched("+", "+", is_upstream=True)
    assert perm_base.is_resource_matched("+", "-", is_owner=True)
    assert perm_base.is_resource_matched("-", "-", is_owner=True)
    assert not perm_base.is_resource_matched("-", "-")
    assert not perm_base.is_resource_matched("+", "-")


def test_is_perm_matched():
    assert perm_base.is_perm_matched(ADMIN_PERM,
        {"action": "test", "effect": "allow", "resource": "*"})
    assert not perm_base.is_perm_matched(TEST_ALLOW_PERM_STAR_MIDDLE,
        {"action": "test", "effect": "allow", "resource": "*"})
    assert not perm_base.is_perm_matched(TEST_ALLOW_PERM_STAR_MIDDLE,
        {"action": "test:foo:bar", "effect": "allow", "resource": "*"})
    assert perm_base.is_perm_matched(TEST_ALLOW_PERM_STAR_MIDDLE,
        {"action": "test:bar:foo", "effect": "allow", "resource": "*"})
    assert perm_base.is_perm_matched(TEST_ALLOW_PERM,
        {"action": "test:foo:bar", "effect": "allow", "resource": "*"})
    assert perm_base.is_perm_matched(TEST_ALLOW_PERM_PLUS,
        {"action": "test:bar:foo", "effect": "allow", "resource": "+"},
        is_upstream=True)
    assert perm_base.is_perm_matched(TEST_ALLOW_PERM_PLUS,
        {"action": "test:bar:foo", "effect": "allow", "resource": "-"},
        is_owner=True)
    assert not perm_base.is_perm_matched(TEST_ALLOW_PERM_PLUS,
        {"action": "test:bar:foo", "effect": "allow", "resource": "-"})
    assert perm_base.is_perm_matched(TEST_ALLOW_PERM_MINUS,
        {"action": "test:bar:foo", "effect": "allow", "resource": "-"},
        is_owner=True)
    assert not perm_base.is_perm_matched(TEST_ALLOW_PERM_MINUS,
        {"action": "test:bar:foo", "effect": "allow", "resource": "-"})
    assert not perm_base.is_perm_matched(TEST_DENY_PERM_STAR,
        {"action": "test:bar:foo", "effect": "allow", "resource": "-"})
    assert perm_base.is_perm_matched(TEST_DENY_PERM_STAR,
        {"action": "test:bar:foo", "effect": "deny", "resource": "-"},
        is_owner=True)
    assert perm_base.is_perm_matched(TEST_DENY_PERM_STAR,
        {"action": "test:bar:foo", "effect": "deny", "resource": "*"})


def test_is_perm_allowed():
    assert perm_base.is_perm_allowed([TEST_ALLOW_PERM_STAR],
        {"action": "test:read", "effect": "allow", "resource": "*"})
    assert not perm_base.is_perm_allowed([TEST_ALLOW_PERM_STAR, TEST_DENY_PERM_STAR],
        {"action": "test:read", "effect": "allow", "resource": "*"})
    assert perm_base.is_perm_allowed([TEST_ALLOW_PERM_STAR, TEST_ALLOW_PERM_PLUS],
        {"action": "test:read", "effect": "allow", "resource": "+"},
        is_upstream=True)
    assert perm_base.is_perm_allowed([TEST_ALLOW_PERM_PLUS, TEST_ALLOW_PERM_MINUS],
        {"action": "test:read", "effect": "allow", "resource": "+"},
        is_upstream=True)
    assert perm_base.is_perm_allowed([TEST_ALLOW_PERM_PLUS],
        {"action": "test:read", "effect": "allow", "resource": "-"},
        is_owner=True)
    assert not perm_base.is_perm_allowed([TEST_ALLOW_PERM_MINUS],
        {"action": "test:read", "effect": "allow", "resource": "+"},
        is_upstream=True)
    assert not perm_base.is_perm_allowed([TEST_ALLOW_PERM_MINUS, TEST_DENY_PERM_STAR],
        {"action": "test:read", "effect": "allow", "resource": "-"},
        is_owner=True)
