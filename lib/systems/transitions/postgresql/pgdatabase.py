# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from pguser import PgUser

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

def create_db_trans(id):
  user = id.attributes['user']
  cluster = user.attributes['cluster']
  name = id.attributes['name']
  username = user.attributes['name']
  return cluster.privileged_command_trans(
      name=('create-db', name),
      cmdline=['/usr/bin/createdb', '-e',
        '--encoding', 'UTF8',
        '--owner', username,
        '--', name,
        ], )

def drop_db_trans(id):
  user = id.attributes['user']
  cluster = user.attributes['cluster']
  name = id.attributes['name']
  return cluster.privileged_command_trans(
      name=('drop-db', name),
      cmdline=['/usr/bin/dropdb', '-e',
        '--', name,
        ], )

class PgDatabase(Transition):
  def realize(self):
    # Can't read yet, so force it.
    if self.attributes['state'] == 'present':
      trans = create_db_trans(self.identity)
    else:
      trans = drop_db_trans(self.identity)
    trans.realize()

def register():
  restype = Type('PgDatabase', PgDatabase,
    [
    # XXX We need to auto-create a dependency to this attribute
    AttrType('user',
      identifying=True,
      pytype=PgUser),
    AttrType('name',
      identifying=True,
      pytype=str),
    AttrType('state',
      default_value='present',
      reader=read_state,
      valid_condition=is_valid_state),
  ])
  Registry.get_singleton().transition_types.register(restype)


