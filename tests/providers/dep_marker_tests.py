import typing as t
from unittest.mock import Mock

import pytest
from xdi.markers import Dep
from xdi.providers import DepMarkerProvider as Provider
from xdi.scopes import Scope

from .abc import ProviderTestCase, _T_NewPro

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


_Ta = t.TypeVar("_Ta")
_Tx = t.TypeVar("_Tx")

_T_NewPro = _T_NewPro[Provider]


class CaseConf:
    injects: t.Any
    default: t.Any
    inject_default: t.Union[t.Any, None]





class DepMarkerTests(ProviderTestCase[Provider]):


    expected: dict[Dep, CaseConf] = [
        Dep(_Tx),
        Dep(_Tx, default='[DEFAULT]'),
        Dep(_Tx, default=Dep(_Ta)),
        Dep(_Tx, scope=Dep.ONLY_SELF, default='[DEFAULT]'),
        Dep(_Tx, scope=Dep.ONLY_SELF, default=Dep(_Ta)),
        Dep(_Tx, scope=Dep.SKIP_SELF),
        Dep(_Tx, scope=Dep.SKIP_SELF, default='[DEFAULT]'),
        Dep(_Tx, scope=Dep.SKIP_SELF, default=Dep(_Ta)),
    ]

    @pytest.fixture(params=expected)
    def abstract(self, request):
        return request.param

    @pytest.fixture
    def new_args(self):
        return ()

    def test_resolve(self, cls: type[Provider], abstract: Dep, new: _T_NewPro, mock_scope: Scope):
        if abstract.has_default and  abstract.scope != Dep.SKIP_SELF:
            mock_scope[abstract.abstract] = None

        subject, res = super().test_resolve(cls, abstract, new, mock_scope)

        if abstract.scope == Dep.SKIP_SELF:
            assert res is mock_scope.parent[abstract.abstract]
            assert not res is mock_scope[abstract.abstract]
        elif abstract.has_default:
            if abstract.injects_default:
                assert res is mock_scope[abstract.default.abstract]
            else:
                assert not res is mock_scope[abstract.abstract]
                assert isinstance(res, cls._dependency_class) 

        # expected.injects =
        # assert res is mock_scope[abstract.__default__]
        # assert not res is mock_scope[abstract.__injects__]




# class DepMarkerOnlySelfTests(DepMarkerTests):

#     expected: dict[Dep, CaseConf] = {
#         Dep(_Tx): SimpleNamespace(
            
#         ),
#         Dep(_Tx, default='[DEFAULT]'): SimpleNamespace(
            
#         ),
#         Dep(_Tx, default=Dep(_Ta)): SimpleNamespace(
            
#         ),
#         Dep(_Tx, scope=Dep.ONLY_SELF): SimpleNamespace(
            
#         ),
#         Dep(_Tx, scope=Dep.ONLY_SELF, default='[DEFAULT]'): SimpleNamespace(
            
#         ),
#         Dep(_Tx, scope=Dep.ONLY_SELF, default=Dep(_Ta)): SimpleNamespace(
            
#         ),
#         Dep(_Tx, scope=Dep.SKIP_SELF): SimpleNamespace(

#         ),
#         Dep(_Tx, scope=Dep.SKIP_SELF, default='[DEFAULT]'): SimpleNamespace(
            
#         ),
#         Dep(_Tx, scope=Dep.SKIP_SELF, default=Dep(_Ta)): SimpleNamespace(
            
#         ),
#     }

#     @pytest.fixture(params=expected.keys())
#     def abstract(self, request):
#         return request.param

#     def test_resolve(self, cls: type[Provider], abstract: Dep, new: _T_NewPro, mock_scope: Scope):
#         subject, res = super().test_resolve(cls, abstract, new, mock_scope)
#         expected = self.expected[abstract]
#         # expected.injects =
#         # assert res is mock_scope[abstract.__default__]
#         # assert not res is mock_scope[abstract.__injects__]



# class DepMarkerSkipSelfTests(DepMarkerTests):

#     @pytest.fixture
#     def abstract(self):
#         return Dep(_Tx, scope=Dep.SKIP_SELF)

#     def test_resolve(self, cls: type[Provider], abstract: Dep, new: _T_NewPro, mock_scope: Scope):
#         subject, res = super().test_resolve(cls, abstract, new, mock_scope)
#         assert res is mock_scope.parent[abstract.__injects__]
#         assert not res is mock_scope[abstract.__default__]





# class DepMarkerDataPathTests(DepMarkerTests):
    
#     @pytest.fixture
#     def marker(self):
#         return Dep(_Ta).bar.run(1, 2, 3, k1=1, k2=2).a["list"][2:-2]

#     @pytest.fixture
#     def value_factory(self):
#         return Foo

#     @pytest.fixture
#     def value_setter(self, value_factory, marker: Dep):
#         def fn(*a, **kw):
#             val = value_factory(*a, **kw)
#             self.value = marker.__eval__(val)
#             return val

#         return fn



class Foo:
    a = dict(list=list(range(10)), data=dict(bee="Im a bee"))

    class bar:
        @classmethod
        def run(cls, *args, **kwargs) -> None:
            print(f"ran with({args=}, {kwargs=})")
            return Foo
