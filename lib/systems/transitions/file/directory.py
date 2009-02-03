# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement

# use posixpath for platform-indepent paths
import os
import pwd
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

def is_valid_username(username):
  try:
    pwd.getpwnam(username)
  except OSError:
    return False
  else:
    return True

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
  # Only allow the permission bits and suid stuff.
  return mode == stat.S_IMODE(mode)

def read_owner(id):
  path = id.id_attrs['path']
  return pwd.getpwuid(os.lstat(path).st_uid).pw_name

def read_mode(id):
  path = id.id_attrs['path']
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
    path = self.id_attrs['path']

    if present1:
      if not present0:
        # Create. Will raise if there is a non-dir in the way.
        os.mkdir(path)
      # Update. We're sure it's no symlink, no need to wrap lchmod.
      os.chmod(path, self.wanted_attrs['mode'])
      owner = self.wanted_attrs['owner']
      if owner is not None:
        uid = pwd.getpwnam(owner).pw_uid
        # -1 means no change
        os.lchown(path, uid, -1)
    elif present0:
      # Delete
      os.rmdir(path)

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
        'owner': AttrType(
          none_allowed=True,
          reader=read_owner,
          valid_condition=is_valid_username,
          # XXX References that don't force realisation would be better.
          pytype=str),
        })
  Registry.get_singleton().resource_types.register(restype)


