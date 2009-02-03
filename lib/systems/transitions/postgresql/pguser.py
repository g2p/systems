# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from pgcluster import PgCluster

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs

__all__ = ('register', )


def read_present(id_attrs):
  cluster = id_attrs['cluster']
  name = id_attrs['name']
  return cluster.check_existence('pg_roles', 'rolname', name)

def create_user_trans(id_attrs):
  cluster = id_attrs['cluster']
  name = id_attrs['name']
  return cluster.command_trans(
      cmdline=['/usr/bin/createuser', '-e',
        '-S', '-D', '-R', '-l', '-i',
        '--', name,
        ], )

def drop_user_trans(id_attrs):
  cluster = id_attrs['cluster']
  name = id_attrs['name']
  return cluster.command_trans(
      cmdline=['/usr/bin/dropuser', '-e',
        '--', name,
        ], )

class PgUser(Resource):
  def expand_into(self, rg):
    p0, p1 = self.read_attrs()['present'], self.wanted_attrs['present']
    if (p0, p1) == (False, True):
      tr = rg.add_transition(create_user_trans(self.id_attrs))
    elif (p0, p1) == (True, False):
      tr = rg.add_transition(drop_user_trans(self.id_attrs))
    else:
      tr = None

    if tr is not None:
      cluster = self.id_attrs['cluster']
      if not cluster.wanted_attrs['present']:
        raise ValueError
      rg.add_resource(cluster)
      rg.add_dependency(cluster, tr)

def register():
  restype = ResourceType('PgUser', PgUser,
      id_type={
        'cluster': AttrType(
          default_value=resource('PgCluster'),
          pytype=PgCluster),
        'name': AttrType(
          pytype=str),
        },
      state_type={
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        })
  Registry.get_singleton().resource_types.register(restype)


