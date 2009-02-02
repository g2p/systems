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
  def get_extra_deps(self):
    return (self.id_attrs['cluster'], )

  def place_transitions(self, tg):
    # Caveat:
    # The user could be dropped between place_transitions and realization.
    p0, p1 = self.read_attrs()['present'], self.wanted_attrs['present']
    if (p0, p1) == (False, True):
      tg.add_transition(create_user_trans(self.id_attrs))
    elif (p0, p1) == (True, False):
      tg.add_transition(drop_user_trans(self.id_attrs))

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


