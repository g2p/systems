# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from pguser import PgUser

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

def create_db_trans(id_attrs):
  user = id_attrs['user']
  cluster = user.id_attrs['cluster']
  name = id_attrs['name']
  username = user.id_attrs['name']
  return cluster.privileged_command_trans(
      cmdline=['/usr/bin/createdb', '-e',
        '--encoding', 'UTF8',
        '--owner', username,
        '--', name,
        ], )

def drop_db_trans(id_attrs):
  user = id_attrs['user']
  cluster = user.id_attrs['cluster']
  name = id_attrs['name']
  return cluster.privileged_command_trans(
      cmdline=['/usr/bin/dropdb', '-e',
        '--', name,
        ], )

class PgDatabase(Resource):
  def place_extra_deps(self, resource_graph):
    resource_graph.add_dependency(self.id_attrs['user'], self)

  def place_transitions(self, transition_graph):
    # Can't read yet, so force it.
    if self.wanted_attrs['state'] == 'present':
      trans = create_db_trans(self.id_attrs)
    else:
      trans = drop_db_trans(self.id_attrs)
    transition_graph.add_transition(trans)

def register():
  restype = ResourceType('PgDatabase', PgDatabase,
      id_type={
        'user': AttrType(
          pytype=PgUser),
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


