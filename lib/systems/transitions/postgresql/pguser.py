# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from pgcluster import PgCluster

from systems.registry import Registry
from systems.realizable import Transition
from systems.typesystem import Type, AttrType

__all__ = ('register', )

def read_state(id):
  cluster = id.attributes['cluster']
  name = id.attributes['name']
  # Tweak Command to get retval
  # ['/usr/bin/psql', '-t', '-c', "SELECT COUNT(*) FROM pg_roles WHERE rolname = '$name'", '|', 'grep', '-q', '1', ],

def is_valid_state(state):
  return state in ('present', 'absent', )

def create_user_trans(id):
  cluster = id.attributes['cluster']
  name = id.attributes['name']
  return cluster.privileged_command_trans(
      name=('create-user', name),
      cmdline=['/usr/bin/createuser', '-e',
        '-S', '-D', '-R', '-l', '-i',
        '--', name,
        ], )

def drop_user_trans(id):
  cluster = id.attributes['cluster']
  name = id.attributes['name']
  return self.privileged_command_trans(
      name=('drop-user', name),
      cmdline=['/usr/bin/dropuser', '-e',
        '--', name,
        ], )

class PgUser(Transition):
  def ensure_extra_deps(self, context):
    context.ensure_dependency(self, self.attributes['cluster'])

  def realize(self):
    # Can't read yet, so force it.
    if self.attributes['state'] == 'present':
      trans = create_user_trans(self.identity)
    else:
      trans = drop_user_trans(self.identity)
    trans.realize()

def register():
  restype = Type('PgUser', PgUser,
    [
    AttrType('cluster',
      identifying=True,
      pytype=PgCluster),
    AttrType('name',
      identifying=True,
      pytype=str),
    AttrType('state',
      default_value='present',
      reader=read_state,
      valid_condition=is_valid_state),
  ])
  Registry.get_singleton().transition_types.register(restype)


