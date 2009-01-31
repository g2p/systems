# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.realizable_dsl import transition

class PgCluster(object):
  """
  A postgresql database cluster.

  Specified by PGHOST and PGPORT;
  note those are not strictly a hostname or a port number.
  """

  # Consider conninfo strings; problem is createuser doesn't support them.
  # Also they do a bit too much.

  def __init__(self, pg_host='/var/run/postgresql', pg_port=5432):
    self.pg_host = pg_host
    self.pg_port = pg_port

  def extra_env(self):
    return {
        'PGHOST': self.pg_host,
        'PGPORT': str(self.pg_port),
        }

  def package_trans(self):
    return transition('AptitudePackage',
        name='postgresql')

  def command_trans(self, **kwargs):
    e = kwargs.get('extra_env', {})
    e.update(self.extra_env())
    kwargs['extra_env'] = e
    # XXX Depends on package_trans
    return transition('Command',
        **kwargs)

  def privileged_command_trans(self, **kwargs):
    if 'username' in kwargs:
      raise ValueError
    kwargs['username'] = 'postgres'
    return self.command_trans(**kwargs)

  def psql_eval_trans(self, sql):
    """
    No prepared statement, so make sure your SQL is injection-free.
    """

    if not isinstance(sql, str):
      raise TypeError
    return self.command_trans(
        cmdline=['/usr/bin/psql', '-At1', '-f', '-', ], cmdline_input=sql)

def register():
  pass

