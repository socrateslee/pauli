# -*- coding:utf-8 -*-
'''
Basic root blueprint entry point.
'''
import flask
import flask_session
import mongoengine
from .common import conf, pauli_root


def setup_pauli(flask_app, url_prefix="/pauli"):
    # setup mongodb
    for alias, attrs in conf.MONGO.items():
        mongoengine.register_connection(alias, **attrs)

    # setup session
    session_db = mongoengine.connection.get_db(alias="pauli")
    config_dict = {
        "SESSION_COOKIE_NAME": conf.SESSION_COOKIE_NAME,
        "SESSION_TYPE": "mongodb",
        "SESSION_MONGODB": session_db.client,
        "SESSION_MONGODB_DB": session_db.name,
        "SESSION_MONGODB_COLLECT": "sessions",
        "PERMANENT_SESSION_LIFETIME": conf.PAULI_SESSION_LIFETIME
    }
    flask_app.config.update(config_dict)
    flask_session.Session(flask_app)

    # import sub level path routings
    from .user.views import api
    from .auth.views import api
    from .auth.views import web
    from .perm.views import api

    # bind pauli blueprint
    flask_app.register_blueprint(pauli_root, url_prefix=url_prefix)

__ALL__ = ['pauli_root', 'conf', 'setup_pauli']
