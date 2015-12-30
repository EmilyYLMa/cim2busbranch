from pypower import idx_bus
import numpy as np


from cim2busbranch import bus_type, Bus, Generator, Branch, Case


def pytest_funcarg__case(request):
    """
    Creates a Case comprising two buses, one generator and one branch between
    the buses.

    """
    # Create the Case
    base_mva = 1

    bus1 = Bus('spam', btype=bus_type.PQ, pd=1, qd=2, base_kv=3, vm=4, va=5,
            vm_max=6, vm_min=7, gs=8, bs=9, area=10, zone=11)
    bus2 = Bus('eggs', btype=bus_type.REF, pd=12, qd=13, base_kv=14, vm=15,
            va=16, vm_max=17, vm_min=18, gs=19, bs=20, area=21, zone=22)
    bus_ids = {bus1: 1, bus2: 2}

    gen = Generator(bus1, '', pg=1, qg=2, pg_min=3, pg_max=4, qg_min=5,
            qg_max=6, vg=7, base_mva=8, online=True, pc1=9, pc2=10,
            qc1_min=11, qc1_max=12, qc2_min=13, qc2_max=14, ramp_agc=15,
            ramp_10=16, ramp_30=17, ramp_q=18, apf=19)

    branch = Branch(bus1, bus2, 'spam', r=1, x=2, b=3, rate_a=4, rate_b=5,
            rate_c=6, ratio=7, angle=8, angle_min=9, angle_max=10, online=True,
            p_from=11, q_from=12, p_to=13, q_to=14)

    case = Case(base_mva=base_mva, buses=[bus1, bus2], generators=[gen],
            branches=[branch])
    case.bus_ids = bus_ids

    return case


def pytest_funcarg__ppc(request):
    """
    Creates the respective PYPOWER case for :func:`pytest_func_arg__case`.

    """
    case = pytest_funcarg__case(None)

    base_mva = case.base_mva
    bus_ids = case.bus_ids

    bus_types = {
        bus_type.PQ: idx_bus.PQ,
        bus_type.REF: idx_bus.REF,
    }
    buses = np.array([
            [
                bus_ids[b], bus_types[b.btype], b.pd, b.qd, b.gs, b.bs,
                b.area, b.vm, b.va, b.base_kv, b.zone, b.vm_max, b.vm_min,
            ] for b in case.buses], dtype=float)

    gens = np.array([
            [
                bus_ids[g.bus], g.pg, g.qg, g.qg_max, g.qg_min, g.vg,
                g.base_mva, g.online, g.pg_max, g.pg_min, g.pc1, g.pc2,
                g.qc1_min, g.qc1_max, g.qc2_min, g.qc2_max, g.ramp_agc,
                g.ramp_10, g.ramp_30, g.ramp_q, g.apf,
            ] for g in case.generators], dtype=float)

    branches = np.array([
            [
                bus_ids[b.from_bus], bus_ids[b.to_bus], b.r, b.x, b.b,
                b.rate_a, b.rate_b, b.rate_c, b.ratio, b.angle, b.online,
                b.angle_min, b.angle_max, b.p_from, b.q_from, b.p_to, b.q_to,
            ] for b in case.branches], dtype=float)

    ppc = {
        'version': '2',
        'baseMVA': base_mva,
        'bus': buses,
        'gen': gens,
        'branch': branches,
    }

    return ppc
