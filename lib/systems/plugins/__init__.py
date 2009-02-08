# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def register():
  from . import base
  base.register()
  from . import files
  files.register()
  from . import packages
  packages.register()
  from . import postgresql
  postgresql.register()
  from . import rails
  rails.register()
  from . import runit
  runit.register()
  from . import subversion
  subversion.register()


