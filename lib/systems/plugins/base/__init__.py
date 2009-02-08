# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def register():
  from . import command
  command.register()
  from . import pythoncode
  pythoncode.register()
  from . import user
  user.register()


