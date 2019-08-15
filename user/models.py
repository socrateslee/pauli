import datetime
import logging
import six
import flask
from mongoengine import *

logger = logging.getLogger(__name__)


class User(Document):
    meta = {"db_alias": "pauli",
            "indexes": ['keywords']}
    created = DateTimeField(required=True, default=datetime.datetime.now)
    state = StringField(default='normal')
    soft_del = BooleanField(default=False)
    name = StringField()
    info = DictField()
    keywords = ListField()

    def save(self):
        UserAuditLog.record(self)
        self.keywords = []
        if self.name:
            self.keywords.append(self.name)
        if self.id:
            self.keywords.append(str(self.id))
        for v in self.info.values():
            if v and isinstance(v, six.string_types) and len(v) <= 32 :
                self.keywords.append(v.strip())
        Document.save(self)


class UserAuditLog(Document):
    meta = {"db_alias": "pauli"}
    created = DateTimeField(required=True, default=datetime.datetime.now)
    user_id = StringField(required=True)
    collection_name = StringField()
    editor_id = StringField()
    editor_name = StringField()
    editor_info = DictField()
    fields = ListField()
    delta = ListField()

    @classmethod
    def record(cls, doc, user_id_field_name=None):
        collection_name = doc._collection.name\
                          if doc._collection else str(doc)
        if user_id_field_name:
            user_id = getattr(doc, user_id_field_name)
        elif collection_name == 'user':
            user_id = str(doc.id)
        else:
            user_id = getattr(doc, 'user_id')
        if not user_id:
            return
        if not getattr(doc, '_changed_fields', None):
            return
        ua_log = UserAuditLog(user_id=user_id,
                              collection_name=collection_name,
                              fields=doc._changed_fields,
                              delta=[])
        for i in doc._delta():
            if not i:
                continue
            for k, v in i.items():
                ua_log.delta.append([k, v])
        try:
            if flask.request:
                ua_log.editor_id = str(flask.request.user.id)
                ua_log.editor_name = flask.request.user.name
                ua_log.editor_info = {}
                ua_log.editor_info.update(flask.request.headers)
        except Exception as e:
            logger.exception(e)

        try:
            ua_log.save()
        except Exception as e:
            logger.exception(e)
