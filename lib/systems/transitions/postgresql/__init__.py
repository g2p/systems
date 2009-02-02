# vim: set fileencoding=utf-8 sw=2 ts=2 et :

def register():
  # Order is important because of default_values.
  import pgcluster
  pgcluster.register()
  import pguser
  pguser.register()
  import pgdatabase
  pgdatabase.register()


