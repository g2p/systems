# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs


def extra_env(id_attrs):
  pg_host = id_attrs['pg_host']
  pg_port = id_attrs['pg_port']
  return {
      'PGHOST': pg_host,
      'PGPORT': str(pg_port),
      }


class PgCluster(Resource):
  """
  A postgresql database cluster.

  Specified by PGHOST and PGPORT;
  note those are not strictly a hostname or a port number.
  """

  def get_extra_deps(self):
    # Also: pg_createcluster, pg_deletecluster
    present = self.wanted_attrs['present']
    pkg_state = { True: 'installed', False: 'purged', }[present]
    pkg = resource('AptitudePackage', name='postgresql')
    return (pkg, )

  def command_trans(self, **kwargs):
    e = kwargs.get('extra_env', {})
    e.update(extra_env(self.id_attrs))
    kwargs['extra_env'] = e
    return transition('Command', **kwargs)

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
  # Consider conninfo strings; problem is createuser doesn't support them.
  # However, they do a bit too much (spec the db…) and wouldn't be identifying.

  restype = ResourceType('PgCluster', PgCluster,
    id_type={
      'pg_host': AttrType(
        default_value='/var/run/postgresql',
        pytype=str),
      'pg_port': AttrType(
        default_value=5432,
        pytype=int),
      },
    state_type={
      'present': AttrType(
        default_value=True,
        pytype=bool),
      })
  Registry.get_singleton().resource_types.register(restype)


