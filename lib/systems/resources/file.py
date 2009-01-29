# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement

# use posixpath for platform-indepent paths
import os

from systems.registry import Registry
from systems.realizable import Resource
from systems.typesystem import Type, AttrType
from systems.util.syscalls import fchmod

__all__ = ('register', )

class File(Resource):
  """
  A file in the filesystem.
  """

  @classmethod
  def register(cls):
    cls.__restype = Type('File', cls,
      [
      AttrType('path',
        identifying=True,
        valid_condition=cls.is_valid_path),
      # Not specifying contents means the file will be emptied.
      AttrType('contents',
        default_value='',
        valid_condition=cls.is_valid_contents),
      AttrType('state',
        default_value='present',
        valid_condition=cls.is_valid_state),
      AttrType('mode',
        default_value=0600,
        valid_condition=cls.is_valid_mode),
    ])
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_path(cls, path):
    """
    Only absolute paths are accepted.
    """

    return os.path.isabs(path)

  @classmethod
  def is_valid_contents(cls, contents):
    # A byte string, no encoding
    return isinstance(contents, str)

  @classmethod
  def is_valid_state(cls, state):
    return state in ('present', 'absent', )

  @classmethod
  def is_valid_mode(cls, mode):
    # Only allow the {u,g,o}{r,w,x} combinations
    return mode == (mode & 0777)

  def get_state(self):
    """
    The state of the file: present or absent.
    """

    # Broken symlinks still are 'present'
    if os.path.lexists(self.attributes['path']):
      return 'present'
    else:
      return 'absent'

  def realize(self):
    # Don't let files be accessible between creation and permission setting.
    os.umask(0077)
    s0, s1 = self.get_state(), self.attributes['state']

    if s1 == 'present':
      # create or update
      with open(self.attributes['path'], 'wb') as f:
        f.write(self.attributes['contents'])
        fchmod(f.fileno(), self.attributes['mode'])
    elif s0 == 'present':
      # delete
      os.unlink(self.attributes['path'])

def register():
  File.register()

