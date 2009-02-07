# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, EResource
from systems.util.templates import build_and_render


def extra_env(id_attrs):
  pg_host = id_attrs['pg_host']
  pg_port = id_attrs['pg_port']
  return {
      'PGHOST': pg_host,
      'PGPORT': str(pg_port),
      }


class PgCluster(EResource):
  """
  A postgresql database cluster.

  Specified by PGHOST and PGPORT;
  note those are not strictly a hostname or a port number.
  """

  def expand_into(self, rg):
    # Also: pg_createcluster, pg_deletecluster
    if not self.wanted_attrs['present']:
      return
    rg.add_resource(resource('AptitudePackage', name='postgresql'))

  def command_trans(self, **kwargs):
    if 'username' not in kwargs:
      # The default admin user on debian
      kwargs['username'] = 'postgres'

    e = kwargs.get('extra_env', {})
    e.update(extra_env(self.id_attrs))
    kwargs['extra_env'] = e

    return transition('Command', **kwargs)

  def psql_eval_trans(self, sql, **kwargs):
    """
    No prepared statement, so make sure your SQL is injection-free.
    """

    if not isinstance(sql, str):
      raise TypeError
    return self.command_trans(
        cmdline=['/usr/bin/psql', '-At1', '-f', '-', ],
        cmdline_input=sql,
        **kwargs)

  def check_existence(self, table, column, value):
    # XXX quoting. Jinja2 doesn't have the relevant filters.
    sql = build_and_render("""
      SELECT EXISTS(
        SELECT * FROM "{{ table }}" WHERE "{{ column }}" = '{{ value }}'
        )""",
      table=table, column=column, value=value)
    sql = sql.encode('utf8')
    cmd = self.psql_eval_trans(sql, redir_stdout=True)
    stdout = cmd.realize()['stdout'].strip()
    assert stdout in ('t', 'f', )
    exists = stdout == 't'
    return exists

def register():
  # Considered conninfo strings; problem is createuser doesn't support them.
  # They do a bit too much (spec the db…) and wouldn't be identifying.
  # Rejected.

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


