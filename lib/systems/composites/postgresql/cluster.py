# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.resource import ensure_resource
from systems.transition import ensure_transition, ref_transition

class Cluster(object):
  """
  A postgresql database cluster.

  Specified by PGHOST and PGPORT;
  those are not strictly a hostname or a port number.

  TODO: nightly backups. Needs cron resource.
  /usr/bin/pg_dump -Fc -f /var/backups/postgresql/$name-\$(date --rfc-3339=date)
  """

  # Consider conninfo strings; problem is createuser doesn't support them.
  # Also they do a bit too much.

  # Decide what contexts are really for because they are a hassle.

  def __init__(self, pg_host='/var/run/postgresql', pg_port=5432):
    self.pg_host = pg_host
    self.pg_port = pg_port

  def extra_env(self):
    return {
        'PGHOST': self.pg_host,
        'PGPORT': str(self.pg_port),
        }

  def ensure_package(self, context):
    return ensure_resource('AptitudePackage',
        context=context, name='postgresql')

  def ensure_command(self, context, **kwargs):
    e = kwargs.get('extra_env', {})
    e.update(self.extra_env())
    kwargs['extra_env'] = e
    return ensure_transition('Command', context=context,
        depends=[self.ensure_package(context=context)],
        **kwargs)

  def ensure_command_privileged(self, context, **kwargs):
    if 'username' in kwargs:
      raise ValueError
    kwargs['username'] = 'postgres'
    return self.ensure_command(context, **kwargs)

  def ensure_psql_eval(self, context, sql):
    """
    No prepared statement, so make sure your SQL is injection-free.
    """

    if not isinstance(sql, str):
      raise TypeError
    return self.ensure_command(context,
        cmdline=['/usr/bin/psql', '-1', '-f', '-', ], cmdline_input=sql)

  # User check:
  # ['/usr/bin/psql', '-t', '-c', "SELECT COUNT(*) FROM pg_roles WHERE rolname = '$name'", '|', 'grep', '-q', '1', ],
  def ensure_create_user(self, context, username):
    return self.ensure_command_privileged(context,
        name=('create-user', username),
        cmdline=['/usr/bin/createuser', '-e',
          '-S', '-D', '-R', '-l', '-i',
          '--', username,
          ], )

  def ensure_drop_user(self, context, username):
    return self.ensure_command_privileged(context,
        name=('drop-user', username),
        cmdline=['/usr/bin/dropuser', '-e',
          '--', username,
          ], )

  def ensure_create_database(self, context, db, owner):
    db_trans = self.ensure_command_privileged(context,
        name=('create-db', db),
        cmdline=['/usr/bin/createdb', '-e',
          '--encoding', 'UTF8',
          '--owner', owner,
          '--', db,
          ], )
    user_trans = ref_transition('Command', context,
        name=('create-user', owner))
    context.add_dependency(db_trans, user_trans)
    return db_trans

  def ensure_drop_database(self, context, db):
    return self.ensure_command_privileged(context,
        name=('drop-db', db),
        cmdline=['/usr/bin/dropdb', '-e',
          '--', db,
          ], )

