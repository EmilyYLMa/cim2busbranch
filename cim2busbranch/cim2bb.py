# encoding: utf-8
from PyCIM import RDFXMLReader

from cim2busbranch import topology


class Converter(object):
    """
    The *Converter* transforms a CIM topology in *cim_file* into a
    bus/branch topology.

    *cim_file* is the path to an XML/RDF encoded CIM topology.

    """
    # Create a topological node (bus) for each one-terminal primary equipment
    _primary_one_t = [
        'TransformerWinding',
        'EnergySource',
        'EnergyConsumer',
        'Connector',  # BusbarSection, Junction
        'RegulatingCondEq',
    ]

    # Create a branch for each two-terminal primary equipment
    _primary_two_t = [
        'Conductor',  # DC-/ACLineSegment
        'SeriesCompensator',
    ]

    # One-terminal secondary equipment can safely be ignored
    _secondary_one_t = [
        'Ground',
    ]

    # Search two-terminal for neighboring connectivity nodes for amalgamation
    _secondary_two_t = [
        'RectifierInverter',
        'Switch',
    ]

    def __init__(self, cim_file):
        self.cim_file = cim_file

        xmlns = RDFXMLReader.xmlns(cim_file)
        self._package_map = RDFXMLReader.get_cim_ns(xmlns)[1]

        self._prim_onet = self._get_equipment_cls(Converter._primary_one_t)
        self._prim_twot = self._get_equipment_cls(Converter._primary_two_t)
        self._sec_onet = self._get_equipment_cls(Converter._secondary_one_t)
        self._sec_twot = self._get_equipment_cls(Converter._secondary_two_t)

    def transform(self):
        """
        Actually parses the CIM file and transforms its contents.
        A :class:`topology.Case` object is returned.

        """
        cim_objects = RDFXMLReader.cimread(self.cim_file)
        base_power, tnodes, lines = self._iterate_prim_eq(cim_objects)
        self._create_bb_topology(base_power, tnodes, lines)

    def _create_bb_topology(self, base_power, tnodes, lines):
        """
        Creates a :class:`topology.Case` from the identified *base_power*,
        *tnodes* (topological nodes) and *lines*.

        """
        buses, generators, p_transformers = self._create_buses(tnodes)
        branches = self._create_branches(lines, p_transformers, base_power, buses)

        assert isinstance(buses, list)  # TODO: Remove
        return topology.Case(base_power, buses, generators, branches)

    def _create_branches(self, lines, p_transformers, base_mva, buses):
        """
        Creates and returns :class:`topology.Branch` instances for the *lines*
        and Transformers (*p_transformers*).

        """
        branches = []
        for line in lines:
            from_bus, to_bus = [buses[t.ConnectivityNode.TopologicalNode]
                    for t in line.Terminals]

            assert from_bus.base_kv == to_bus.base_kv
            voltage = from_bus.base_kv  # kV

            # Ref. values for p.u. conversion
            z_base = voltage ** 2 / base_mva  # Ohm
            y_base = 1.0 / z_base  # Ohm^-1

            # Maximum current for the line
            # NOTE: The same values is taken for rate_a, rate_b and rate_c!
            limset = line.OperationalLimitSet
            if limset:
                max_i = limset[0].OperationalLimitValue[0].value  # A
                mva_rating = voltage * max_i * 1000  # MVA
            else:
                mva_rating = 999  # MVA, resonable default?


            branches.append(topology.Branch(
                    from_bus, to_bus,
                    name=(line.name or line.mRID),
                    r=(line.r / z_base),
                    x=(line.x / z_base),
                    b=(line.bch / y_base),
                    rate_a=mva_rating,
                    rate_b=mva_rating,
                    rate_c=mva_rating,
                ))

        for pt in p_transformers:
            pass  # TODO: Create branch from transformer - cim14 vs. cim15?

        return branches

    def _create_buses(self, tnodes):
        """
        Creates and returns a :class:`topology.Bus` for each topologial node in
        *tnodes* and handels all connected primary equipment to parameterize
        the bus and/or creat :class:`topology.Generator` instances.

        Power transformers are ignored and handled by
        :meth:`_create_branches`.

        """
        buses = {}
        generators = {}
        power_transformers = set()
        swingbus = None

        for tnode, prim_equip in tnodes.items():
            btype = topology.bus_type.PQ
            names = []
            cim_classes = []
            position_points = set()

            for equip in prim_equip:
                equip_cls = equip.__class__.__name__

                names.append(equip.name or equip.mRID)
                cim_classes.append(equip_cls)
                position_points |= self._get_position_points(equip)

                if (equip_cls == 'BusbarSection' and
                        equip.aliasName == 'SwingBus'):
                    if swingbus:
                        raise RuntimeError('Only one swing bus is allowed. '
                                'Found %s and %s.' % (swingbus, equip))

                    swingbus = equip
                    btype = topology.bus_type.REF

                elif equip_cls == 'TransformerWinding':
                    power_transformers.add(equip.PowerTransformer)

                # Todo: Check other equipment classes
            base_voltage = self._get_base_voltage(tnode)

            # TODO: Check for loads and generators
            buses[tnode] = topology.Bus(
                    name=', '.join(sorted(names)),
                    btype=btype,
                    base_kv=base_voltage,
                    pd=0.0,
                    qd=0.0,
                    vm=1.0,
                    va=0.0,
                    cim_classes=sorted(cim_classes),
                    pos=position_points,
                )

        assert swingbus, 'No swing bus found.'

        return buses, generators, power_transformers

    def _get_position_points(self, equipment):
        """
        Returns the set of position points (:class:`topology.Point`) for
        *equipment*.

        """
        loc = equipment.Location
        if not loc:
            return set()

        pos = set([topology.Point(float(p.xPosition), float(p.yPosition))
                for p in loc.PositionPoints])

        return pos

    def _get_base_voltage(self, tnode):
        """
        Tries to get a base voltage value from *tnode* (a topological node) or
        from it’s connectivity nodes.

        Raises a :class:`ValueError` if no base voltage can be found or if
        the base voltages of the c. nodes deffer from each other.

        """
        if tnode.BaseVoltage:
            return tnode.BaseVoltage.nominalVoltage

        if (hasattr(tnode.ConnectivityNodeContainer, 'BaseVoltage') and
                tnode.ConnectivityNodeContainer.BaseVoltage):
            return tnode.ConnectivityNodeContainer.BaseVoltage.nominalVoltage

        base_voltage = None
        for cn in tnode.ConnectivityNodes:
            if not cn.ConnectivityNodeContainer or not hasattr(
                    cn.ConnectivityNodeContainer, 'BaseVoltage'):
                continue

            bv = cn.ConnectivityNodeContainer.BaseVoltage.nominalVoltage
            if not bv:
                continue

            if not base_voltage:
                base_voltage = bv
            elif bv != base_voltage:
                raise ValueError('Base voltage %s of %s deffers from %s' %
                        (bv, cn.mRID, base_voltage))

        if base_voltage:
            return base_voltage

        raise ValueError('No base voltage found for topo. node (%s)' %
                ', '.join(cn.mRID for cn in tnode.ConnectivityNodes))

    def _iterate_prim_eq(self, cim_objects):
        """
        Iterates over all *cim_objects* and creates a topological node for
        every one-terminal primary equipment.

        """
        processed = set()  # Contain all proccessed connectivity nodes
        tnode_equipment = {}  # Top. nodes and adjacent equipment
        lines = set()  # Contains all lines
        base_power = None

        BasePower = self._get_cls('BasePower')
        TopologicalNode = self._get_cls('TopologicalNode')

        for mrid, obj in cim_objects.items():
            if isinstance(obj, BasePower):
                assert not base_power, (
                        'There should be only one BasePower instance.')
                base_power = obj.basePower

            elif isinstance(obj, self._prim_onet):
                assert len(obj.Terminals) == 1, ('%s has %d terminals, but '
                        'should only have 1.' % (obj.mRID, len(obj.Terminals)))

                term = obj.Terminals[0]
                cnode = term.ConnectivityNode
                if cnode in processed:
                    tnode = cnode.TopologicalNode
                else:
                    tnode = TopologicalNode()
                    self._process_cnode(tnode, term, processed)

                # Append obj to the tnodes equipment
                tnode_equipment.setdefault(tnode, []).append(obj)

            elif isinstance(obj, self._prim_twot):
                assert len(obj.Terminals) == 2, ('%s has %d terminals, but '
                        'should only have 2.' % (obj.mRID, len(obj.Terminals)))
                lines.add(obj)

            # else: continue

        return base_power, tnode_equipment, lines

    def _process_cnode(self, tnode, src_terminal, processed):
        """
        Recursively processes the connectivity node connected to *src_terminal*
        and adds it to terminals.

        You need to pass the terminal and not the connectivity node, because
        we need the terminal to keep track where we’re coming from and to not
        visit the same terminal again.

        """
        cnode = src_terminal.ConnectivityNode
        if cnode in processed:
            return

        tnode.addConnectivityNodes(cnode)
        processed.add(cnode)

        for terminal in cnode.Terminals:
            if terminal is src_terminal:
                continue

            ce = terminal.ConductingEquipment

            # Recursivly process other nodes if the terminal connects to a
            # rectifier inverter or a closed switch.
            if (isinstance(ce, self._get_cls('RectifierInverter')) or
                    (isinstance(ce, self._get_cls('Switch')) and
                                        (not ce.normalOpen or ce.retain))):
                assert len(ce.Terminals) == 2

                other_term = ce.Terminals[1] if terminal is ce.Terminals[0] \
                        else ce.Terminals[0]

                self._process_cnode(tnode, other_term, processed)

    def _get_equipment_cls(self, names):
        """Returns a touple containing the class objects for *names*."""
        return tuple(self._get_cls(name) for name in names)

    def _get_cls(self, name):
        """Imports and returns the class object for *name*."""
        module = __import__(self._package_map[name], globals(), locals(),
                [name])

        return getattr(module, name)
