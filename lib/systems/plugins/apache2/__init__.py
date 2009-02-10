# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def register():
  from . import a2mod
  a2mod.register()
  from . import a2site
  a2site.register()
  from . import passengersite
  passengersite.register()


