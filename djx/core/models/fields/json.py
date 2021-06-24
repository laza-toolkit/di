import typing as t 
from collections.abc import Callable
from django.db import models as m
from django.db.models.fields.json import KeyTransform
from django.db.models.query_utils import DeferredAttribute

from djx.common import json
from djx.common.collections import MappingObject
from djx.common.utils import export


class _RawJson(str):
    __slots__ = ()

@export()
class JSONField(m.JSONField):
    """JSONField Object"""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        # Some backends (SQLite at least) extract non-string values in their
        # SQL datatypes.
        if isinstance(expression, KeyTransform) and not isinstance(value, str):
            return value
        return self.value_from_json(value)

    def value_from_json(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return _RawJson(value)

    def get_prep_value(self, value):
        if value is None or isinstance(value, _RawJson):
            return value
        return json.dumps(value).decode()

    def validate(self, value, model_instance):

        m.Field.validate(self, value, model_instance)
        
        try:
            json.dumps(value)
        except TypeError:
            raise m.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )

    def formfield(self, **kwargs):
        return m.Field.formfield(self, **kwargs)




class JSONObjectDescriptor(DeferredAttribute):

    field: 'JSONObjectField'
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        name = self.field.attname
        try:
            return obj.__dict__[name]
        except KeyError:
            self.__set__(obj, super().__get__(obj, cls))
            return obj.__dict__[name]

    def __set__(self, obj, val):
        obj.__dict__[self.field.attname] = self.field.coerce_value(val,try_default=True)

    def __delete__(self, obj):
        try:
            del obj.__dict__[self.field.attname]
        except KeyError:
            pass
        


_T_JSONObject = t.TypeVar('_T_JSONObject', json.Jsonable, MappingObject)
_T_ObjectFactory = Callable[[t.Optional[t.Any]], _T_JSONObject]

@export()
class JSONObjectField(JSONField, t.Generic[_T_JSONObject]):
    """JSONObjectField """

    descriptor_class = JSONObjectDescriptor
    empty_strings_allowed = False
    
    def __init__(self, 
                *args, 
                type: type[_T_JSONObject]=MappingObject, 
                factory:_T_ObjectFactory = None, 
                **kwargs) -> None:
        self.object_type = type
        self.object_factory = factory
        super().__init__(*args, **kwargs)
    
    # def get_internal_type(self):
    #     return 'JSONField'

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        
        if self.object_type is not MappingObject:
            kwargs['type'] = self.object_type

        if self.object_factory is not None:
            kwargs['factory'] = self.object_factory

        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if value is None or isinstance(expression, KeyTransform):
            return value
        return self.coerce_value(value)

    def coerce_value(self, value: t.Any, *, try_default:bool=False) -> _T_JSONObject:
        cls = self.object_type
        if isinstance(value, cls) or (value is None and self.null):
            return value
        
        if isinstance(value, str):
            value = self.value_from_json(value)

        func = self.object_factory or cls
        if try_default is True and value is None and self.blank:
            return (self.has_default() and self.get_default or func)()
        else:
            return func(value)
