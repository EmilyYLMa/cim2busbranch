from os.path import dirname, join

from PyCIM import RDFXMLReader
import pytest

from cim2busbranch import cim2bb


cases = {
    'TestCaseB.xml': {
        'base_power': 10,
        'num_tnodes': 4,
        'num_lines': 4,
        'num_transformers': 0,
        'bus_attr': sorted([
            ('Industry 2, Transformer20kV', 3, 0, 0, 1, 0,
                ['BusbarSection', 'EnergyConsumer'], set([(0, 2)])),
            ('PV, Residential', 1, 0, 0, 1, 0,
                ['EnergyConsumer', 'EnergySource'], set([(5, 2)])),
            ('WEC', 1, 0, 0, 1, 0,
                ['SynchronousMachine'], set([(1, 0)])),
            ('Industry', 1, 0, 0, 1, 0,
                ['EnergyConsumer'], set([(4, 0)])),
        ]),
        'branch_attr': sorted([
        ]),
    },
    'TestCaseB_gen.xml': {
        'base_power': 10,
        'num_tnodes': 4,
        'num_lines': 4,
        'num_transformers': 0,
        'bus_attr': sorted([
            ('Transformer20kV', 3, 0, 0, 1, 0, ['BusbarSection'], set()),
            ('Bus1', 1, 0, 0, 1, 0, ['BusbarSection'], set()),
            ('Bus2', 1, 0, 0, 1, 0, ['BusbarSection'], set()),
            ('Bus3', 1, 0, 0, 1, 0, ['BusbarSection'], set()),
        ]),
        'branch_attr': sorted([
        ]),
    },
    'Transformer.xml': {
        'base_power': 1,
        'num_tnodes': 4,
        'num_lines': 1,
        'num_transformers': 2,
        'bus_attr': sorted([
            ('Busbar17kV, GenAlpha, PT_17132_W1, PT_1733_W1', 3, 0, 0, 1, 0,
                ['BusbarSection', 'SynchronousMachine', 'TransformerWinding',
                'TransformerWinding'], set()),
            ('LoadA, PT_1733_W2', 1, 0, 0, 1, 0, ['EnergyConsumer',
                'TransformerWinding'], set()),
            ('LoadB', 1, 0, 0, 1, 0, ['EnergyConsumer'], set()),
            ('PT_17132_W2', 1, 0, 0, 1, 0, ['TransformerWinding'], set()),
        ]),
        'branch_attr': sorted([
        ]),
    },
}


def pytest_generate_tests(metafunc):
    """
    Creates a test case for each entry of the *cases* dict.

    """
    if 'converter' in metafunc.funcargnames:
        for case in cases.keys():
            metafunc.addcall(param=case)


def pytest_funcarg__converter(request):
    """
    Creates a class:`cim2bb.Converter` instance for the current test case.

    """
    cim_file = join(dirname(__file__), 'data', request.param)
    return cim2bb.Converter(cim_file)


def pytest_funcarg__results(request):
    """
    Returns the expected results for the current test case.

    """
    return cases[request.param]


# -----------------------------------------------------------------------------
# Real testing starts here
# -----------------------------------------------------------------------------
def test_convertet_init(converter, results):
    assert isinstance(converter._package_map, dict) and converter._package_map
    assert [cls.__name__ for cls in converter._prim_onet] == [
        'TransformerWinding',
        'EnergySource',
        'EnergyConsumer',
        'Connector',
        'RegulatingCondEq',
    ]
    assert [cls.__name__ for cls in converter._prim_twot] == [
        'Conductor',
        'SeriesCompensator',
    ]
    assert [cls.__name__ for cls in converter._sec_onet] == [
        'Ground',
    ]
    assert [cls.__name__ for cls in converter._sec_twot] == [
        'RectifierInverter',
        'Switch',
    ]


def test_create_branches(converter, results):
    cim_objects = RDFXMLReader.cimread(converter.cim_file)
    base_power, tnodes, lines = converter._iterate_prim_eq(cim_objects)
    buses, gens, pt = converter._create_buses(tnodes)

    branches = converter._create_branches(lines, pt, base_power, buses)
    assert branches == results['branch_attr']


def test_create_buses(converter, results):
    cim_objects = RDFXMLReader.cimread(converter.cim_file)
    base_power, tnodes, lines = converter._iterate_prim_eq(cim_objects)

    buses, gens, pt = converter._create_buses(tnodes)
    data = sorted([
            (b.name, b.btype, b.pd, b.qd, b.vm, b.va, b.cim_classes, b.pos)
                for b in buses.values()
        ])
    print data
    print results['bus_attr']
    assert data == results['bus_attr']

    assert gens == {}
    assert len(pt) == results['num_transformers']


def test_get_position_points(converter, results):
    get_cls = converter._get_cls
    BusbarSection = get_cls('BusbarSection')
    Location = get_cls('Location')
    PositionPoint = get_cls('PositionPoint')

    bs = BusbarSection()
    pp = converter._get_position_points(bs)
    assert pp == set()

    loc = Location()
    bs.Location = loc
    pp = converter._get_position_points(bs)
    assert pp == set()

    loc.addPositionPoints(PositionPoint(xPosition=1, yPosition=2))
    pp = converter._get_position_points(bs)
    assert pp == set([(1, 2)])

    loc.addPositionPoints(PositionPoint(xPosition=2, yPosition=2))
    pp = converter._get_position_points(bs)
    assert pp == set([(1, 2), (2, 2)])


def test_get_base_voltage(converter, results):
    get_cls = converter._get_cls
    TopologicalNode = get_cls('TopologicalNode')
    ConnectivityNode = get_cls('ConnectivityNode')
    VoltageLevel = get_cls('VoltageLevel')
    BaseVoltage = get_cls('BaseVoltage')

    base_voltage = BaseVoltage(nominalVoltage=0.4)
    voltage_level = VoltageLevel(BaseVoltage=base_voltage)

    cnodes = [ConnectivityNode() for i in range(3)]
    tnode = TopologicalNode(ConnectivityNodes=cnodes)

    pytest.raises(ValueError, converter._get_base_voltage, tnode)

    tnode.BaseVoltage = base_voltage
    assert converter._get_base_voltage(tnode) == base_voltage.nominalVoltage
    tnode.BaseVoltage = None

    tnode.ConnectivityNodeContainer = voltage_level
    assert converter._get_base_voltage(tnode) == base_voltage.nominalVoltage
    tnode.ConnectivityNodeContainer = None

    for cn in cnodes:
        cn.ConnectivityNodeContainer = voltage_level
    assert converter._get_base_voltage(tnode) == base_voltage.nominalVoltage

    cnodes[0].ConnectivityNodeContainer = VoltageLevel(
            BaseVoltage=BaseVoltage(nominalVoltage=20))
    pytest.raises(ValueError, converter._get_base_voltage, tnode)


def test_iterate_primary_equipment(converter, results):
    cim_objects = RDFXMLReader.cimread(converter.cim_file)
    base_power, tnodes, branches = converter._iterate_prim_eq(cim_objects)

    assert base_power == results['base_power']

    assert len(tnodes) == results['num_tnodes']
    for tnode, equip in tnodes.items():
        assert tnode.__class__.__name__ == 'TopologicalNode'
        assert len(equip) >= 1

    assert len(branches) == results['num_lines']
    for branch in branches:
        assert branch.__class__.__name__ == 'ACLineSegment'


def test_process_cnode():
    # _process_cnode() is covered by test_iterate_primary_equipment()
    assert True


def test_get_equipment_cls(converter):
    res = converter._get_equipment_cls(('Terminal', 'ConnectivityNode'))
    assert (res[0].__name__, res[1].__name__) == (
            'Terminal', 'ConnectivityNode')


def test_get_cls(converter):
    Cls = converter._get_cls('Terminal')
    assert Cls.__name__ == 'Terminal'
