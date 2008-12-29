#!/usr/bin/env python
from __future__ import with_statement

from distutils.core import setup, Command

class debian_substvars(Command):
     description = 'Print distutils metadata in deb-substvars(5) format.'
     user_options = [('file=', None, 'The substvars file to append to' ), ]

     def initialize_options(self):
          self.file = None

     def finalize_options(self):
          if self.file is None:
               raise 'Must give the file option'

     @classmethod
     def fixup_description(cls, s):
          lines = s.splitlines()
          r = lines[0] + '${Newline}'
          for l in lines[1:-1]:
               r += '${Space}' + l + '${Newline}'
          if len(lines) > 1:
               r += '${Space}' + lines[-1]
          return r

     def run(self):
          m = self.distribution.metadata
          with open(self.file, 'a') as f:
               f.write('distutils:Description=%s\n' % \
                         m.get_description())
               f.write('distutils:Long-Description=%s\n' % \
                         self.fixup_description(m.get_long_description()))

setup(name='Systems',
      version='0.1',
      author='Gabriel de Perthuis',
      author_email='g2p.code@gmail.com',
      description='a declarative language for managing system resources',
      long_description='Systems allows you to write a declarative description\n'
        +'of the resources that make up a system,\n'
        +'and enforce this description.\n',
      requires=['networkx', ],
      packages=['systems', 'systems.resources', ],
      package_dir={'': 'lib'},
      cmdclass={'debian_substvars': debian_substvars, },
     )
