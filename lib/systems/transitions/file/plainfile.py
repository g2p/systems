# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import
from __future__ import with_statement

# use posixpath for platform-indepent paths
import os
import stat

from . import fileperms

from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, EResource

__all__ = ('register', )


def read_contents(id):
  path = id.id_attrs['path']
  with open(path) as f:
    return f.read()

def read_present(id_attrs):
  """
  Whether there is a _regular file_ with that name.
  """

  return fileperms.read_present(id_attrs, stat.S_ISREG)


class PlainFile(fileperms.FilePermsMixin, EResource):
  """
  A regular plain file in the filesystem.
  """

  def expand_into(self, rg):
    # Had to rename it to avoid a clash.
    return self.fp_expand_into(rg)

  def create(self):
    with open(self.id_attrs['path'], 'wb') as f:
      pass
    # writing is done later.

  def update(self):
    with open(self.id_attrs['path'], 'wb') as f:
      f.write(self.wanted_attrs['contents'])

  def delete(self):
    os.unlink(self.id_attrs['path'])

def register():
  restype = ResourceType('PlainFile', PlainFile,
      id_type={
        'path': AttrType(
          pytype=str,
          valid_condition=fileperms.is_valid_path),
        },
      state_type={
        # Not specifying contents means the file will be emptied.
        'contents': AttrType(
          default_value='',
          reader=read_contents,
          # A byte string, no encoding
          pytype=str),

        # The rest is handled with fileperms
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        'mode': AttrType(
          default_value='0600',
          reader=fileperms.read_mode,
          valid_condition=fileperms.is_valid_mode,
          pytype=str),
        'owner': AttrType(
          none_allowed=True,
          reader=fileperms.read_owner,
          valid_condition=fileperms.is_valid_username,
          # XXX Non-realizing references would be nice.
          # eg by building a ref if a res is passed, and depending on the ref.
          pytype=str),
        'group': AttrType(
          none_allowed=True,
          reader=fileperms.read_group,
          valid_condition=fileperms.is_valid_groupname,
          pytype=str),
        })
  Registry.get_singleton().resource_types.register(restype)


