from logging import getLogger

from cim2busbranch.topology import bus_type, Bus, Generator, Branch, Case


__all__ = [
    '__version__',
    'logger',
    'transform',
    'pypower_case',
    'bus_type',
    'Bus',
    'Generator',
    'Branch',
    'Case',
]

__version__ = '0.1'
logger = getLogger('cim2pylon')


def transform(cim):
    """
    Transforms a CIM topology into the bus/branch model and returns a
    :class:`cim2busbranch.topology.Case`.

    If *cim* is a string, :func:`PyCIM.cimread` will be called first to create
    the topology.

    """
    from cim2busbranch import cim2bb

    if isinstance(cim, basestring):
        import PyCIM
        cim = PyCIM.cimread(cim)

    return cim2bb.transform(cim)


def run_pypower(case):
    """
    Executes a PYPOWER power flow for *case* and writes its results back to
    *case*.

    If *case* is a string, :func:`transform` will be called first to create
    a bus/branch model from the CIM file.

    """
    from pypower.api import ppoption, runpf
    from cim2busbranch import ext_pypower

    if isinstance(case, basestring):
        case = transform(case)

    ppc = ext_pypower.create(case)

    ppo = ppoption(OUT_ALL=0, VERBOSE=0)
    res = runpf(ppc, ppo)

    if not res[1]:
        raise RuntimeError('PYPOWER power flow failed.')

    ext_pypower.write_results_to_case(res[0], case)
