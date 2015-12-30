=============
Cim2BusBranch
=============

Tansforms `PyCIM <http://pycim.org/>`_ CIM topologies to a generic bus/branch
model that can be used to perform load flow analyses with `PYPOWER
<http://pypower.org/>`_.


Requirements
============

Cim2BusBranch runs on Python >= 2.6 and requires `PyCIM <http://pycim.org/>`_.
`PYPOWER <http://pypower.org/>`_ is not mandatory but maybe sensible to also be
installed.

To run the tests, you need `pytest <http://pytest.org/latest/>`_ and `mock
<http://www.voidspace.org.uk/python/mock/>`_.


Installation
============

You can install Cim2BusBranch easily via `PIP
<http://pypi.python.org/pypi/pip>`_ (or ``easy_install``)::

    $ pip install cim2busbranch
    $ # or:
    $ easy_install cim2busbranch

You can also download and install Cim2BusBranch manually::

    $ cd where/you/put/cim2busbranch/
    $ python setup.py install


Cim2BusBranch
=============

The Documentation can be found in the *docs/* directory or `online
<http://stefan.sofa-rockers.org/docs/cim2busbranch/>`_.
