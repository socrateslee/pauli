import datetime
from mongoengine.queryset.queryset import QuerySet


class DefineQuerySet(QuerySet):

    def update(self, upsert=False, multi=True, write_concern=None,
               full_result=False, **update):
        if hasattr(self._document, "lut"):
            update["lut"] = datetime.datetime.now()
        super(DefineQuerySet, self).update(
            upsert, multi, write_concern, full_result, **update)

    def modify(self, upsert=False, full_response=False, remove=False, new=False, **update):
        if hasattr(self._document, "lut"):
            update["lut"] = datetime.datetime.now()
        super(DefineQuerySet, self).modify(
            upsert, full_response, remove, new, **update)


def change_lut_on_save(document_class):
    '''
    A decorator for Document sub classes.
    If the class have lut field, change it to
    current datetime when save function is called.
    '''
    original_save = document_class.save
    if hasattr(document_class, 'update'):
        original_update = document_class.update
    if hasattr(document_class, 'modify'):
        original_modify = document_class.modify

    def save_with_lut(self, **kw):
        if hasattr(self, 'lut'):
            self.lut = datetime.datetime.now()
        return original_save(self, **kw)

    def update_with_lut(self, **kw):
        if hasattr(self, 'lut'):
            kw["lut"] = datetime.datetime.now()
        original_update(self, **kw)

    def modify_with_lut(self, query=None, **update):
        if hasattr(self, 'lut'):
            update['lut'] = datetime.datetime.now()
        if query is None:
            query = {}
        return original_modify(self, query=query, **update)

    document_class.save = save_with_lut
    document_class._meta["queryset_class"] = DefineQuerySet
    if hasattr(document_class, 'modify'):
        document_class.modify = modify_with_lut
    if hasattr(document_class, 'update'):
        document_class.update = update_with_lut
    return document_class
