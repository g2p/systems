# vim: set fileencoding=utf-8 sw=2 ts=2 et :

def register():
  import pgcluster
  pgcluster.register()
  import pgdatabase
  pgdatabase.register()
  import pgdbbackup
  pgdbbackup.register()
  import pguser
  pguser.register()


