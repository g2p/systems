#!/usr/bin/env python
from distutils.core import setup

setup(name='Systems',
      version='0.1',
      author='Gabriel de Perthuis',
      author_email='g2p.code@gmail.com',
      packages=['systems', 'systems.resources', ],
      package_dir={'systems': 'src'}
     )
