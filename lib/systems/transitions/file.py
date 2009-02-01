# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement

# use posixpath for platform-indepent paths
import os
import stat

from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.dsl import transition
from systems.util.syscalls import fchmod

__all__ = ('register', )

class File(Resource):
  """
  A file in the filesystem.
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('File', cls,
        id_type={
          'path': AttrType(
            valid_condition=cls.is_valid_path),
          },
        state_type={
          # Not specifying contents means the file will be emptied.
          'contents': AttrType(
            default_value='',
            reader=cls.read_contents,
            # A byte string, no encoding
            pytype=str),
          'state': AttrType(
            default_value='present',
            reader=cls.read_state,
            valid_condition=cls.is_valid_state),
          'mode': AttrType(
            default_value=0600,
            reader=cls.read_mode,
            valid_condition=cls.is_valid_mode),
          })
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_path(cls, path):
    """
    Only absolute paths are accepted.
    """

    return os.path.isabs(path)

  @classmethod
  def read_contents(cls, id):
    path = id.id_attrs['path']
    with open(path) as f:
      return f.read()

  @classmethod
  def is_valid_state(cls, state):
    return state in ('present', 'absent', )

  @classmethod
  def read_state(cls, id_attrs):
    """
    The state of the file: present or absent.
    """

    path = id_attrs['path']
    # Broken symlinks still are 'present'
    if os.path.lexists(path):
      return 'present'
    else:
      return 'absent'

  @classmethod
  def is_valid_mode(cls, mode):
    # Only allow the permission bits.
    # Disallow suid stuff for now.
    return mode == (stat.S_IMODE(mode) & 0777)

  @classmethod
  def read_mode(cls, id):
    path = id.id_attrs['path']
    # May return invalid mode.
    # I think it's ok; invalid modes may exist, we just don't set them.
    return stat.S_IMODE(os.lstat(path).st_mode)

  def place_transitions(self, transition_graph):
    code = transition('PythonCode', function=self.realize)
    transition_graph.add_transition(code)
    return code

  def realize(self):
    # Don't let files be accessible between creation and permission setting.
    os.umask(0077)
    s0, s1 = self.read_state(self.id_attrs), self.wanted_attrs['state']

    if s1 == 'present':
      # create or update
      with open(self.id_attrs['path'], 'wb') as f:
        f.write(self.wanted_attrs['contents'])
        fchmod(f.fileno(), self.wanted_attrs['mode'])
    elif s0 == 'present':
      # delete
      os.unlink(self.id_attrs['path'])

def register():
  File.register()

