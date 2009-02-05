# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def register():
  from . import svnworkingcopy
  svnworkingcopy.register()


