# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import runpy


def load_plugin(pkg_name):
  # The __init__ module is used because of http://bugs.python.org/issue2751
  # Weird messages with python 2.5 and absolute_import,
  # clear refusal to execute a package in 2.6 and 3.0.
  runpy.run_module(pkg_name + '.__init__')['register']()


