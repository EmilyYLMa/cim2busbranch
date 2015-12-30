#!/usr/bin/env python
# encoding: utf-8
from distutils.core import setup

import cim2busbranch


setup(
    name='Cim2BusBranch',
    version=cim2busbranch.__version__,
    author='Stefan Scherfke',
    author_email='stefan at sofa-rockers.org',
    description=('Tansforms CIM topologies into a bus/branch model for '
                 'load flow analyses'),
    long_description=open('README.txt').read(),
    url='https://bitbucket.org/ssc/cim2busbranch/',
    download_url='https://bitbucket.org/ssc/cim2busbranch/downloads/',
    license='Simpliefied BSD',
    packages=[
        'cim2busbranch',
    ],
    package_data={},
    install_requires=[
        'PyCIM>=15.13.3',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
    ],
)
