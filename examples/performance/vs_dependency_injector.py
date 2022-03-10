"""Dependency Injector Factory providers benchmark."""

from functools import reduce
from operator import or_

from dependency_injector import containers, providers, wiring
from laza.di import Injector, context, inject

from _benchmarkutil import Benchmark

N = int(.1e6)

res: dict[str, tuple[float, float]] = {}


class A(object):
    def __init__(self):
        pass


class B(object):
    def __init__(self, a: A, /):
        assert isinstance(a, A)


class C(object):
    def __init__(self, a: A, /, b: B):
        assert isinstance(a, A)
        assert isinstance(b, B)


class Test(object):
    def __init__(self, a: A, /, b: B, c: C):

        assert isinstance(a, A)
        assert isinstance(b, B)
        assert isinstance(c, C)

        self.a = a
        self.b = b
        self.c = c


ioc = Injector()

ioc.factory(A)
ioc.factory(B)#.singleton()
ioc.factory(C)#.singleton()
ioc.factory(Test).args(A())  # .singleton()


# Singleton = providers.Singleton 
Singleton = providers.Factory 

class Container(containers.DeclarativeContainer):
    a = providers.Factory(A)
    b = Singleton(B, a)
    c = Singleton(C, a, b=b)
    test = providers.Factory(
        Test,
        A(),
        b=b,
        c=c,
    )


@inject
def _inj_laza(test: Test, a: A, b: B, c: C):
    assert isinstance(test, Test)
    assert isinstance(a, A)
    assert isinstance(b, B)
    assert isinstance(c, C)


@wiring.inject
def _inj_di(
    test: Test = wiring.Provide[Container.test],
    a: Test = wiring.Provide[Container.a],
    b: Test = wiring.Provide[Container.b],
    c: Test = wiring.Provide[Container.c],
):
    assert isinstance(test, Test)
    assert isinstance(a, A)
    assert isinstance(b, B)
    assert isinstance(c, C)


c = Container()
c.wire([__name__])


def main():
    with context(ioc) as ctx:
       

        ls = []
       
        
        bench = Benchmark("A.", N).run(di=Container.a, laza=ctx[A])
        ls.append(bench)
        print(bench, "\n")

        bench = Benchmark("B.", N).run( di=Container.b, laza=ctx[B])
        ls.append(bench)
        print(bench, "\n")

        bench = Benchmark("C.", N).run(di=Container.c, laza=ctx[C])
        ls.append(bench)
        print(bench, "\n")

        bench = Benchmark("Test.", N).run(di=Container.test, laza=ctx[Test])
        ls.append(bench)
        print(bench, "\n")


        bench = Benchmark(f"Providers[{A | B | C | Test}]", N)
        bench |= reduce(or_, ls)
        print(bench, "\n")

        # b = Benchmark("inject.", N).run(di=_inj_di, laza=_inj_laza)
        # print(b, "\n")


if __name__ == '__main__':
    main()
