# -*- coding:utf-8 -*-
'''
Basic root blueprint entry point.
'''
import os
import flask
import flask_session
import mongoengine
from . import conf
from . import event
from .exceptions import PauliException


pauli_root = flask.Blueprint("pauli_root", __name__,
                             template_folder=os.path.abspath(os.path.dirname(__file__) + '/../templates'))

__ALL__ = ['pauli_root', 'conf', 'event', 'PauliException']
