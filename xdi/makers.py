import operator
import typing as t
from abc import ABC, abstractmethod
from collections import namedtuple
from enum import IntEnum

import attr
from typing_extensions import Self

from . import Injectable, T_Default, T_Injectable, T_Injected
from ._common import Missing, private_setattr
from ._common.lazy import LazyOp as BaseLazyOp

if t.TYPE_CHECKING:
    from .scopes import Scope


class InjectionMarker(Injectable, t.Generic[T_Injectable]):

    __slots__ = ()

    @property
    @abstractmethod
    def __origin__(self):
        ...


class InjectionDescriptor(Injectable, t.Generic[T_Injectable]):

    __slots__ = ()

    @property
    @abstractmethod
    def __abstract__(self) -> T_Injectable:
        ...


class DepScope(IntEnum):

    any: "DepScope" = 0
    """Inject from any scope.
    """

    only_self: "DepScope" = 1
    """Only inject from the current scope without considering parents
    """

    skip_self: "DepScope" = 2
    """Skip the current scope and resolve from it's parent instead.
    """


_object_new = object.__new__


@InjectionMarker.register
@private_setattr
class PureDep(t.Generic[T_Injectable]):
    __slots__ = ("abstract",)

    abstract: T_Injected

    scope: t.Final = DepScope.any
    default: t.Final = Missing
    has_default: t.Final = False
    injects_default: t.Final = False

    def __new__(cls: type[Self], abstract: T_Injectable) -> Self:
        if abstract.__class__ is cls:
            return abstract
        self = _object_new(cls)
        self.__setattr(abstract=abstract)
        return self

    def forward_op(op):
        def method(self: Self, *a):
            return op(self.abstract, *a)

        return method

    # @property
    # def __dependency__(self):
    #     return self.abstract

    __eq__ = forward_op(operator.eq)
    __ne__ = forward_op(operator.ne)

    __gt__ = forward_op(operator.gt)
    __ge__ = forward_op(operator.ge)

    __lt__ = forward_op(operator.lt)
    __le__ = forward_op(operator.le)

    __hash__ = forward_op(hash)
    __bool__ = forward_op(bool)

    del forward_op

    @property
    def provided(self):
        return Provided(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.abstract!s})"

    def __init_subclass__(cls, *args, **kwargs):
        raise TypeError(f"Cannot subclass {cls.__module__}.{cls.__name__}")


_AbcDepTuple = namedtuple(
    "Dep", ("abstract", "scope", "default"), defaults=[DepScope.any, Missing]
)


_pure_dep_defaults = PureDep.scope, PureDep.default


@InjectionMarker.register
@private_setattr
class Dep(_AbcDepTuple):

    """Marks an injectable as a `dependency` to be injected."""

    __slots__ = ()

    abstract: T_Injectable
    scope: DepScope
    default: T_Default
    Scope = DepScope

    ANY_SCOPE: t.Final = DepScope.any
    """Inject from any scope.
    """

    ONLY_SELF: t.Final = DepScope.only_self
    """Only inject from the current scope without considering parents
    """

    SKIP_SELF: t.Final = DepScope.skip_self
    """Skip the current scope and resolve from it's parent instead.
    """

    def __init_subclass__(cls, *args, **kwargs):
        raise TypeError(f"Cannot subclass {cls.__module__}.{cls.__name__}")

    def __subclasscheck__(self, sub: type) -> bool:
        return sub is PureDep or self._base_subclasscheck(sub)

    _base_subclasscheck = _AbcDepTuple.__subclasscheck__

    def __new__(
        cls: type[Self],
        dependency: T_Injectable,
        scope: DepScope = ANY_SCOPE,
        default=Missing,
    ):
        if _pure_dep_defaults == (scope, default):
            return PureDep(dependency)
        else:
            return _AbcDepTuple.__new__(cls, dependency, scope, default)

    @property
    def __origin__(self):
        return self.__class__

    @property
    def has_default(self):
        return not self.default is Missing

    @property
    def injects_default(self):
        return isinstance(self.default, InjectionMarker)

    @property
    def provided(self):
        return Provided(self)




@InjectionMarker.register
@InjectionDescriptor.register
class Provided(BaseLazyOp):

    __slots__ = ()
    __offset__ = 1

    @t.overload
    def __new__(cls: type[Self], abstract: type[T_Injected]) -> Self:
        ...

    __new__ = BaseLazyOp.__new__

    @property
    def __abstract__(self) -> type[T_Injected]:
        return self.__expr__[0]

    @property
    def __origin__(self):
        return self.__class__