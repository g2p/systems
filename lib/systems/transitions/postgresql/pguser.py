# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from pgcluster import PgCluster

from systems.dsl import transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs

__all__ = ('register', )

def read_state(id_attrs):
  cluster = id_attrs['cluster']
  name = id_attrs['name']
  # Tweak Command to get retval
  # ['/usr/bin/psql', '-t', '-c', "SELECT COUNT(*) FROM pg_roles WHERE rolname = '$name'", '|', 'grep', '-q', '1', ],

def is_valid_state(state):
  return state in ('present', 'absent', )

def create_user_trans(id_attrs):
  cluster = id_attrs['cluster']
  name = id_attrs['name']
  return cluster.privileged_command_trans(
      cmdline=['/usr/bin/createuser', '-e',
        '-S', '-D', '-R', '-l', '-i',
        '--', name,
        ], )

def drop_user_trans(id_attrs):
  cluster = id_attrs['cluster']
  name = id_attrs['name']
  return cluster.privileged_command_trans(
      cmdline=['/usr/bin/dropuser', '-e',
        '--', name,
        ], )

class PgUser(Resource):
  def place_extra_deps(self, resource_graph):
    resource_graph.add_dependency(self.id_attrs['cluster'], self)

  def place_transitions(self, transition_graph):
    # Can't read yet, so force it.
    if self.wanted_attrs['state'] == 'present':
      trans = create_user_trans(self.id_attrs)
    else:
      trans = drop_user_trans(self.id_attrs)
    transition_graph.add_transition(trans)
    return trans

def register():
  restype = ResourceType('PgUser', PgUser,
      id_type={
        'cluster': AttrType(
          pytype=PgCluster),
        'name': AttrType(
          pytype=str),
        },
      state_type={
        'state': AttrType(
          default_value='present',
          reader=read_state,
          valid_condition=is_valid_state),
        })
  Registry.get_singleton().resource_types.register(restype)


