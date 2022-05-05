import asyncio
from threading import Lock, Thread
import typing as t
from unittest.mock import MagicMock, Mock, patch
import attr
import pytest


from collections import abc


from xdi.exceptions import InjectorError
from xdi.graph import DepGraph
from xdi.scopes import ContextScope

from .. import checks

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


_T = t.TypeVar('_T')
_T_FnNew = abc.Callable[..., ContextScope]


from .scope_tests import test_setup_multiple_times, test_reset_multiple_times


@pytest.fixture
def new_args(MockContainer: type[DepGraph]):
    return MockContainer(),

@pytest.fixture
def cls():
    return ContextScope



def test_basic(new: _T_FnNew):
    sub = new()
    assert isinstance(sub, ContextScope)
    



async def test_setup_multiple_async(new: _T_FnNew, cls: type[ContextScope], MockInjector):

    N, L = 5, int(1e4)

    with patch.object(cls, '_new_injector'):
        cls._new_injector = MagicMock(wraps=MockInjector)
        sub = new()

        res = [None] * N
            
        async def func(n):
            res[n] = sub.is_active, sub.injector()

        tasks = [func(i) for i in range(N)]
        
        await asyncio.gather(*tasks)
        
        assert not sub.is_active

        seen = set()
        for i, (active, val) in enumerate(res):
            print(f'{i} -> {active=}, {val=}')
            assert not active
            assert not val in seen
            seen.add(val)

        assert sub._new_injector.call_count == N



async def test_parent_context_setup(new: _T_FnNew, cls: type[ContextScope], MockInjector):

    N, L = 5, int(1e4)

    with patch.object(cls, '_new_injector'):
        cls._new_injector = MagicMock(wraps=MockInjector)
        sub = new()

        res = [None] * N
            
        async def func(n):
            res[n] = sub.is_active, sub.injector()

        tasks = [func(i) for i in range(N)]

        inj = sub.setup()

        await asyncio.gather(*tasks)
        
        seen = set()
        for i, (active, val) in enumerate(res):
            assert active
            assert val is inj
            assert not i or val in seen
            seen.add(val)

        sub._new_injector.assert_called_once()
        sub.reset()




def _test_in_multithread_setup(new: _T_FnNew, cls: type[ContextScope], MockInjector):

    N, L = 4, int(1e4)

    def load_fn(s: int=L):
        load = [*range(int(s))]

    def load_mock():
        load_fn()
        inj = MockInjector()
        inj.close =MagicMock(wraps=load_fn)
        return inj

    with patch.object(cls, '_new_injector'):
        cls._new_injector = MagicMock(wraps=load_mock)
        sub = new()

        res = [None] * N
            
        def func(n):
            res[n] = sub.is_active, sub.injector()

        threads = [Thread(target=func, args=(i,)) for i in range(N)]
        
        *(t.start() for t in threads), 
        *(t.join() for t in threads),
        

        seen = set()
        for i, (active, val) in enumerate(res):
            print(f'{i} -> {active=}, {val=}')
            # if i == 0:
            #     assert not active
            # else:
            #     assert active or locked
            #     assert val in seen
            seen.add(val)
        
        sub.reset()
        sub._new_injector.assert_called_once()


@xfail(raises=InjectorError, strict=True)
def test__set_current_injector_multiple_times(new: _T_FnNew, MockInjector):
    sub = new()
    sub._set_current_injector(MockInjector())
    sub._set_current_injector(MockInjector())