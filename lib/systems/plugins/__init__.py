# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def register():
  from . import command
  command.register()
  from . import files
  files.register()
  from . import packages
  packages.register()
  from . import postgresql
  postgresql.register()
  from . import pythoncode
  pythoncode.register()
  from . import rails
  rails.register()
  from . import subversion
  subversion.register()
  from . import user
  user.register()


