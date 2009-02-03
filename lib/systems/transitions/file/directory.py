# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement

# use posixpath for platform-indepent paths
import os
import stat

from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.dsl import transition

__all__ = ('register', )


def is_valid_path(path):
  """
  Only absolute paths are accepted.
  """

  return os.path.isabs(path)

def read_present(id_attrs):
  """
  Whether the file must exist.
  """

  path = id_attrs['path']
  try:
    st = os.lstat(path)
  except OSError:
    # Does not exist
    return False
  else:
    # True if dir,
    # False if something that is not a dir.
    return bool(stat.S_ISDIR(st.st_mode))

def is_valid_mode(mode):
  # Only allow the permission bits.
  # Disallow suid stuff for now.
  return mode == (stat.S_IMODE(mode) & 0777)

def read_mode(id):
  path = id.id_attrs['path']
  # May return invalid mode.
  # I think it's ok; invalid modes may exist, we just don't set them.
  return stat.S_IMODE(os.lstat(path).st_mode)


class Directory(Resource):
  """
  A directory in the filesystem.
  """

  def place_transitions(self, transition_graph):
    code = transition('PythonCode', function=self._realize)
    transition_graph.add_transition(code)
    return code

  def _realize(self):
    # Don't let files be accessible between creation and permission setting.
    os.umask(0077)
    present0 = self.read_attrs()['present']
    present1 = self.wanted_attrs['present']

    if present1:
      if not present0:
        # Create. Will raise if there is a non-dir in the way.
        os.mkdir(self.id_attrs['path'])
      # Update. We're sure it's no symlink, no need to wrap lchmod.
      os.chmod(self.id_attrs['path'], self.wanted_attrs['mode'])
    elif present0:
      # Delete
      os.rmdir(self.id_attrs['path'])

def register():
  restype = ResourceType('Directory', Directory,
      id_type={
        'path': AttrType(
          valid_condition=is_valid_path),
        },
      state_type={
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        'mode': AttrType(
          default_value=0700,
          reader=read_mode,
          valid_condition=is_valid_mode),
        })
  Registry.get_singleton().resource_types.register(restype)


