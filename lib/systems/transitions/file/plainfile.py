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


def is_valid_path(path):
  """
  Only absolute paths are accepted.
  """

  return os.path.isabs(path)

def read_contents(id):
  path = id.id_attrs['path']
  with open(path) as f:
    return f.read()

def read_present(id_attrs):
  """
  Whether the file must exist.
  """

  path = id_attrs['path']
  # Broken symlinks still are 'present'
  return os.path.lexists(path)

def is_valid_mode(mode):
  # Only allow the permission bits.
  # Disallow suid stuff for now.
  return mode == (stat.S_IMODE(mode) & 0777)

def read_mode(id):
  path = id.id_attrs['path']
  # May return invalid mode.
  # I think it's ok; invalid modes may exist, we just don't set them.
  return stat.S_IMODE(os.lstat(path).st_mode)


class PlainFile(Resource):
  """
  A file in the filesystem.
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
      # create or update
      with open(self.id_attrs['path'], 'wb') as f:
        f.write(self.wanted_attrs['contents'])
        fchmod(f.fileno(), self.wanted_attrs['mode'])
    elif present0:
      # delete
      os.unlink(self.id_attrs['path'])

def register():
  restype = ResourceType('PlainFile', PlainFile,
      id_type={
        'path': AttrType(
          valid_condition=is_valid_path),
        },
      state_type={
        # Not specifying contents means the file will be emptied.
        'contents': AttrType(
          default_value='',
          reader=read_contents,
          # A byte string, no encoding
          pytype=str),
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        'mode': AttrType(
          default_value=0600,
          reader=read_mode,
          # Beware: octal is error-prone
          pytype=int,
          valid_condition=is_valid_mode),
        })
  Registry.get_singleton().resource_types.register(restype)


