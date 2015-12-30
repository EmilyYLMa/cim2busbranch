from mock import Mock
from pytest import raises

from cim2busbranch.topology import bus_type, Bus, Generator, Branch, Case


def test_bus_type():
    assert len(bus_type) == 4
    assert bus_type.PQ == 1
    assert bus_type.PV == 2
    assert bus_type.REF == 3
    assert bus_type.ISOLATED == 4


def test_bus():
    bus = Bus()

    # Check if setting and restoring the original values works
    def assert_orig():
        assert bus.pd_orig == pd_orig
        assert bus.qd_orig == qd_orig

    pd_orig = bus.pd
    qd_orig = bus.qd

    assert_orig()

    bus.pd = 3
    bus.qd = 2

    assert_orig()

    bus.reset()

    assert_orig()
    assert bus.pd == bus.pd_orig
    assert bus.qd == bus.qd_orig


def test_generator():
    gen = Generator(None, pg=100, qg=50)

    assert gen.pg == 100
    assert gen.pg_max == gen.pg
    assert gen.qg == 50
    assert gen.qg_max == gen.qg

    assert Generator(None, pg=100, qg=100, pg_max=200, qg_max=200)

    raises(ValueError, Generator, None, pg=100, pg_max=50)
    raises(ValueError, Generator, None, qg=100, qg_max=50)

    # Check if setting and restoring the original values works
    def assert_orig():
        assert gen.pg_orig == pg_orig
        assert gen.qg_orig == qg_orig

    pg_orig = gen.pg
    qg_orig = gen.qg

    assert_orig()

    gen.pg = 3
    gen.qg = 2

    assert_orig()

    gen.reset()

    assert_orig()
    assert gen.pg == gen.pg_orig
    assert gen.qg == gen.qg_orig


def test_branch():
    assert Branch(None, None)


def test_case():
    items = [Mock(spec=['reset']) for i in range(6)]
    case = Case(100, items[:3], items[3:6], items[6:])

    case.reset()
    for item in items[:6]:
        item.reset.assert_called_once_with()
