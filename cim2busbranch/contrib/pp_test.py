# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 19:17:37 2015

@author: christianfleischer
"""

# encoding: utf-8
"""
This module contains two example test cases for cim2busbranch and PYPOWER.

"""
import math

from pypower.api import ppoption, runpf

import cim2busbranch as cim2bb
from cim2busbranch import ext_pypower


def test_case_a():
    """
    This test case is taken from Eckard Spring: Elektrische Energienetze
    (2003), pp. 206–212.

          Gen1                Gen2
            +                   +
        Bus1(REF) ––––––––––– Bus2
            \                  /
             \______    ______/
                    \  /
                    Bus3

    """
    base_mva = 1000.0  # MVA
    base_kv = 220.0  # kV

    line_params = {  # All lines have a length of 100 km
        'r': 0.128,  # p.u.
        'x': 0.661,  # p.u.
        'b': 0.01748,  # p.u.
    }

    bus1 = cim2bb.Bus(
        name='Bus 1',
        btype=cim2bb.bus_type.REF,
        base_kv=base_kv,
        vm=1.0,
        va=0.0,
        pd=384.0,  # MW
        qd=288.0,  # MVAr
    )
    gen1 = cim2bb.Generator(
        bus=bus1,
        name='Gen 1',  # Swing
        base_mva=base_mva,
    )

    bus2 = cim2bb.Bus(
        name='Bus 2',
        base_kv=base_kv,
    )
    gen2 = cim2bb.Generator(
        bus=bus2,
        name='Gen 2',
        base_mva=base_mva,
        pg=192.0,  # 192 MW
        qg=140.0,  # 140 MVAr
    )

    bus3 = cim2bb.Bus(
        name='Bus 3',
        base_kv=base_kv,
        pd=216.0,  # 216 MW
        qd=162.0,  # 162 MVAr
    )

    lines = [
        cim2bb.Branch(bus1, bus2, **line_params),
        cim2bb.Branch(bus1, bus3, **line_params),
        cim2bb.Branch(bus2, bus3, **line_params),
    ]

    case = cim2bb.Case(
        base_mva=base_mva,
        buses=[bus1, bus2, bus3],
        branches=lines,
        generators=[gen1, gen2],
    )

    return case


def test_case_b():
    """
    This is an internal test grid that is used for some CIM stuff.

                Grid                      PV
                  +                        +
        Transformer20kV(REF) ––––––––––– Bus1
                  |                        |
                  |                        |
                  |                        |
                Bus2 ––––––––––––––––––– Bus3
                  +
                WECS

    """
    base_mva = 1.0
    base_kv = 20.0  # 20 kV
    base_z = base_kv ** 2 / base_mva  # Ohm
    base_y = 1.0 / base_z  # Ohm^-1

    r = 0.125  # Ohm / km
    x = 0.112  # Ohm / km
    c = 300    # nF / km
    # g = 0.0    # Ohm^-1 / km

    omega = 2 * math.pi * 50
    b = omega * c / (10 ** 9)  # Ohm^-1 / km

    def line_params(length):
        """
        Multiplies the line parameters with the line’s length and translates
        them to per unit values.

        """
        return {
            'r': r * length / base_z,  # p.u.
            'x': x * length / base_z,  # p.u.
            'b': b * length / base_y,  # p.u.
        }

    transformer = cim2bb.Bus(
        name='Transformer20kV',  # Industry 2
        btype=cim2bb.bus_type.REF,
        base_kv=base_kv,
        vm=1.0,
        va=0.0,
        pd=1.76,  # 1.76 MW
        qd=0.95,  # 0.95 MVAr
    )
    grid = cim2bb.Generator(
        bus=transformer,
        name='Grid',
        base_mva=base_mva,
    )

    bus1 = cim2bb.Bus(
        name='Bus1',   # Residential
        base_kv=base_kv,
        pd=0.8,  # 0.8 MW
        qd=0.2,  # 0.2 MVAr
    )
    pv = cim2bb.Generator(
        bus=bus1,
        name='PV',
        base_mva=base_mva,
        pg=0.2,  # 0.2 MW
        qg=0.0,
    )

    bus2 = cim2bb.Bus(
        name='Bus2',
        base_kv=base_kv,
        pd=0.0,
        qd=0.0,
    )
    wecs = cim2bb.Generator(
        bus=bus2,
        name='WECS',
        base_mva=base_mva,
        pg=1.98,  # 1.98 MW
        qg=0.28,  # 0.28 MVAr
    )

    bus3 = cim2bb.Bus(
        name='Bus3',  # Industry
        base_kv=base_kv,
        pd=0.85,  # 0.85 MW
        qd=0.53,  # 0,53 MVAr
    )

    branches = [
        cim2bb.Branch(transformer, bus1, **line_params(5.0)),
        cim2bb.Branch(transformer, bus2, **line_params(3.0)),
        cim2bb.Branch(bus2, bus3, **line_params(0.3)),
        cim2bb.Branch(bus1, bus3, **line_params(2.0)),
    ]

    case = cim2bb.Case(
        base_mva=base_mva,
        buses=[transformer, bus1, bus2, bus3],
        branches=branches,
        generators=[grid, pv, wecs],
    )

    return case


def main():
    import sys

    case = sys.argv[1] if len(sys.argv) == 2 else 'a'
    cases = {
        'a': test_case_a,
        'b': test_case_b,
    }

    case = cases[case]()
    ppc = ext_pypower.create(case)

    ppo = ppoption(OUT_ALL=0, VERBOSE=0)
    res = runpf(ppc, ppo)

    ext_pypower.write_results_to_case(res[0], case)
    print(case)


if __name__ == '__main__':
    main()