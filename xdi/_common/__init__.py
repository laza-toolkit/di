
from copy import deepcopy
from functools import wraps
import inspect
import operator
import sys
import types
import typing as t
from collections import ChainMap
from collections.abc import Callable, Hashable
from importlib import import_module
from typing import ForwardRef, TypeVar
from typing_extensions import Self

import attr


_object_setattr = object.__setattr__
_setattr = setattr

_T = TypeVar('_T')


def ensure_isinstance(*types: type[_T], skip=(), name="", msg="{name} allowed types(s): {allowed}. got: '{type}'."):
    allowed = ', '.join(f"{t.__qualname__!r}" for t in types)
    def ensure(obj):
        if isinstance(obj, types) or obj in skip:
            return obj

        raise TypeError(msg.format(name=name,allowed=allowed, type=f"{obj.__class__.__qualname__!r}"))

    return ensure


def private_setattr(klass=None, *, name: str='setattr', setattr=True, setattr_fn=_object_setattr, frozen: str =None):

    def decorator(cls_):

        def setter(self: Self, name=None, value=None, force=False, /, **kw):
            if not force and frozen and getattr(self, frozen, False):
                setter_ = _setattr
            else:
                setter_ = setattr_fn
            name and kw.setdefault(name. value)
            for k,v in kw.items():
                setter_(self, k, v)
        
        def __setattr__(self: Self, name, value):
            getattr(self, name)
            raise AttributeError(f"`cannot set {name!r} on frozen {self.__class__.__qualname__!r}.")

        _base__init_subclass__ = cls_.__init_subclass__
        
        def __init_subclass__(cls, **kwargs):
            if not hasattr(cls, fn := f'_{cls.__name__}__{name}'):
                _setattr(cls, fn, setter)
            _base__init_subclass__(**kwargs)
        cls_.__init_subclass__ = classmethod(__init_subclass__)

        if not hasattr(cls_, fn := f'_{cls_.__name__}__{name}'):
            _setattr(cls_, fn, setter)

        if setattr and cls_.__setattr__ is _object_setattr:
            cls_.__setattr__ = __setattr__
        
        return cls_

    return decorator if klass is None else decorator(klass)







def calling_frame(depth=1, *, globals: bool=None, locals: bool=None, chain: bool=None):
    """Get the globals() or locals() scope of the calling scope"""

    if None is globals is locals is chain:
        globals = True
    elif (not chain and True is globals is locals) or (False is globals is locals):
        raise ValueError(f'args `globals` and `locals` are mutually exclusive') # pragma: no cover

    try:
        frame = sys._getframe(depth + 1)
        if chain:
            scope = ChainMap(frame.f_locals, frame.f_globals)
        if globals:
            scope = frame.f_globals
        else:
            scope = frame.f_locals
    finally:
        return types.MappingProxyType(scope)




def typed_signature(
    callable: Callable[..., t.Any], *, follow_wrapped=True, globalns=None, localns=None
) -> inspect.Signature:
    sig = inspect.signature(callable, follow_wrapped=follow_wrapped)

    if follow_wrapped:
        callable = inspect.unwrap(
            callable, stop=(lambda f: hasattr(f, "__signature__"))
        )

    if globalns is None:
        globalns = getattr(callable, "__globals__", None) or getattr(
            import_module(callable.__module__), "__dict__", None
        )

    params = (
        p.replace(annotation=eval_type(p.annotation, globalns, localns))
        for p in sig.parameters.values()
    )

    return sig.replace(
        parameters=params,
        return_annotation=eval_type(sig.return_annotation, globalns, localns),
    )


def eval_type(value, globalns, localns=None):

    if isinstance(value, str):
        value = ForwardRef(value)
    try:
        return t._eval_type(value, globalns, localns)
    except NameError:
        # this is ok, it can be fixed with update_forward_refs
        return value




class MissingType:

    __slots__ = ()

    __value__: t.ClassVar['MissingType'] = None

    def __new__(cls):
        return cls.__value__

    @classmethod
    def _makenew__(cls, name):
        if cls.__value__ is None:
            cls.__value__ = object.__new__(cls)
        return cls()

    def __bool__(self): return False

    def __str__(self): return ''

    def __repr__(self): return f'Missing'

    def __reduce__(self):
        return self.__class__, () # pragma: no cover
    
    def __eq__(self, x):
        return x is self

    def __hash__(self):
        return id(self)







Missing = MissingType._makenew__('Missing')






_T_Key = t.TypeVar("_T_Key")
_T_Val = t.TypeVar("_T_Val", covariant=True)
_T_Default = t.TypeVar("_T_Default", covariant=True)


class   frozendict(dict[_T_Key, _T_Val]):

    __slots__ = ("_hash",)

    def not_mutable(self, *a, **kw):
        raise TypeError(f"immutable type: {self} ")

    __delitem__ = __setitem__ = setdefault = not_mutable
    clear = pop = popitem = update = __ior__ = not_mutable
    del not_mutable

    def __hash__(self):
        try:
            ash = self._hash
        except AttributeError:
            ash = None
            items = self._hash_items_()
            if items is not None:
                try:
                    ash = hash(items)
                except TypeError:
                    pass
            _object_setattr(self, '_hash', ash)

        if ash is None:
            raise TypeError(f"un---hashable type: {self.__class__.__name__!r}")

        return ash

    def _hash_items_(self) -> Hashable:
        return *((k, self[k]) for k in sorted(self)),

    def __reduce__(self):
        return (
            self.__class__,
            (dict(self),),
        )

    def copy(self):
        return self.__class__(self)
    __copy__ = copy

    def __deepcopy__(self, memo=None):
        return self.__class__(deepcopy(dict(self), memo))

    __or = dict[_T_Key, _T_Val].__or__

    def __or__(self, o):
        return self.__class__(self.__or(o))
        
