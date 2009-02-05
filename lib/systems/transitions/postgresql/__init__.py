# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def register():
  # Order is important because of default_values.
  from . import pgcluster
  pgcluster.register()
  from . import pguser
  pguser.register()
  from . import pgdatabase
  pgdatabase.register()


