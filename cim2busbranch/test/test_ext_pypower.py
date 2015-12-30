from pypower import idx_bus, idx_gen, idx_brch
import numpy as np

from cim2busbranch import ext_pypower


pytest_plugins = 'cim2busbranch.test.support'


def test_create(case, ppc):
    res = ext_pypower.create(case)

    assert res['version'] == ppc['version']
    assert res['baseMVA'] == ppc['baseMVA']
    assert (res['bus'] == ppc['bus']).all()
    assert (res['gen'] == ppc['gen']).all()
    assert (res['branch'] == ppc['branch']).all()


def test_write_results_to_case(case, ppc):
    ppc['bus'][0][idx_bus.VM] = 0.5
    ppc['bus'][0][idx_bus.VA] = 0.3
    ppc['bus'][1][idx_bus.PD] = 3.4
    ppc['bus'][1][idx_bus.QD] = 4.2

    ppc['gen'][0][idx_gen.PG] = 2.3
    ppc['gen'][0][idx_gen.QG] = 1.7

    ppc['branch'][0][idx_brch.PF] = 1.1
    ppc['branch'][0][idx_brch.QF] = 1.2
    ppc['branch'][0][idx_brch.PT] = 1.3
    ppc['branch'][0][idx_brch.QT] = 1.4

    ext_pypower.write_results_to_case(ppc, case)

    assert case.buses[0].vm == 0.5
    assert case.buses[0].va == 0.3
    assert case.buses[0].pd == 1
    assert case.buses[0].qd == 2
    assert case.buses[1].vm == 15
    assert case.buses[1].va == 16
    assert case.buses[1].pd == 3.4
    assert case.buses[1].qd == 4.2

    assert case.generators[0].pg == 2.3
    assert case.generators[0].qg == 1.7

    assert case.branches[0].p_from == 1.1
    assert case.branches[0].q_from == 1.2
    assert case.branches[0].p_to == 1.3
    assert case.branches[0].q_to == 1.4


def test__make_bus_list(case, ppc):
    ret = ext_pypower._make_bus_list(case)
    assert (ret == ppc['bus']).all()


def test__fill_bus_array(case, ppc):
    for bc, bp in zip(case.buses, ppc['bus']):
        ret = np.zeros(13, dtype=np.float64)
        ext_pypower._fill_bus_array(ret, bc, case.bus_ids[bc])
        assert (ret == bp).all()


def test__make_gen_list(case, ppc):
    ret = ext_pypower._make_gen_list(case.generators, case.bus_ids)
    assert (ret == ppc['gen']).all()


def test__fill_gen_array(case, ppc):
    for gc, gp in zip(case.generators, ppc['gen']):
        ret = np.zeros(21, dtype=np.float64)
        ext_pypower._fill_gen_array(ret, gc, case.bus_ids)
        assert (ret == gp).all()


def test__make_branch_list(case, ppc):
    ret = ext_pypower._make_branch_list(case.branches, case.bus_ids)
    assert (ret == ppc['branch']).all()


def test__fil_branch_array(case, ppc):
    for bc, bp in zip(case.branches, ppc['branch']):
        ret = np.zeros(17, dtype=np.float64)
        ext_pypower._fill_branch_array(ret, bc, case.bus_ids)
        assert (ret == bp).all()
