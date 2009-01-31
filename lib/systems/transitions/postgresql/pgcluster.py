# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.registry import Registry
from systems.realizable import Transition
from systems.realizable_dsl import transition
from systems.typesystem import Type, AttrType


def is_valid_state(state):
  return state in ('present', 'absent', )

def extra_env(identity):
  pg_host = identity.attributes['pg_host']
  pg_port = identity.attributes['pg_port']
  return {
      'PGHOST': pg_host,
      'PGPORT': str(pg_port),
      }


class PgCluster(Transition):
  """
  A postgresql database cluster.

  Specified by PGHOST and PGPORT;
  note those are not strictly a hostname or a port number.
  """

  def realize(self):
    # XXX Not fine grained.
    return transition('AptitudePackage',
        name='postgresql')

  def command_trans(self, **kwargs):
    e = kwargs.get('extra_env', {})
    e.update(extra_env(self.identity))
    kwargs['extra_env'] = e
    # XXX Depends on package_trans
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

  restype = Type('PgCluster', PgCluster,
    [
    AttrType('pg_host',
      identifying=True,
      default_value='/var/run/postgresql',
      pytype=str),
    AttrType('pg_port',
      identifying=True,
      default_value=5432,
      pytype=int),
    AttrType('state',
      default_value='present',
      valid_condition=is_valid_state),
  ])
  Registry.get_singleton().transition_types.register(restype)


