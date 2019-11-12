# -*- coding: utf-8 -*-
'''
Config module for pauli, also containing default config values.
'''


# Default session lifetime
PAULI_SESSION_LIFETIME = 86400

# The cookie name for session id
SESSION_COOKIE_NAME = 'sessionid'

# Automatically create user from Dingtalk signin
DINGTALK_AUTO_CREATE_USER = False

# The primary fields for checking duplication of a Dingtalk user
USER_DINGTALK_PRIMARY_FIELDS = ["jobnumber"]

# The fields that should be synchronized to the field of a user
USER_INFO_DINGTALK_FIELDS = [
    "name",
    "email",
    "orgEmail",
    "mobile",
    "jobnumber",
    "avatar"
]

# Overwrite user's info from dingtalk as the default behavior
USER_INFO_DINGTALK_DEFAULT_OVERWRITE = False
