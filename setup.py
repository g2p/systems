#!/usr/bin/env python
from __future__ import with_statement

from distutils.core import setup, Command

from epydoc.docbuilder import build_doc_index
from epydoc.docwriter.html import HTMLWriter

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
               f.write('distutils:Name=%s\n' % \
                         m.get_name())
               f.write('distutils:Description=%s\n' % \
                         m.get_description())
               f.write('distutils:Long-Description=%s\n' % \
                         self.fixup_description(m.get_long_description()))

class build_doc(Command):
     description = 'Build the API reference using epydoc'
     user_options = []

     def initialize_options(self):
          pass

     def finalize_options(self):
          pass

     def find_items(self):
          """
          Returns a list of package dirnames and module filenames
          for which we should build docs.

          This matches what the build_py command uses.
          """

          # A less deeply integrated solution might be to use
          # the build/ directory.

          items = []
          build_py = self.distribution.get_command_obj('build_py')
          build_py.ensure_finalized()
          if build_py.packages:
               for package in build_py.packages:
                    package_dir = build_py.get_package_dir(package)
                    items.append(package_dir)
          if build_py.py_modules:
               for (package, module, module_file) in build_py.find_modules():
                    items.append(module_file)
          return items

     def run(self):
          m = self.distribution.metadata
          docindex = build_doc_index(self.find_items())
          html_writer = HTMLWriter(
                    docindex,
                    prj_name=m.get_name(),
                    prj_url=m.get_url())

          # Add configurability (via dist metadata)
          html_writer.write('doc/api')

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
      cmdclass={
           'debian_substvars': debian_substvars,
           'build_doc': build_doc,
           },
     )

