# vim: set fileencoding=utf-8 sw=2 ts=2 et :

# use posixpath for platform-indepent paths
import os
import stat

import fileperms

from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource

__all__ = ('register', )


def read_present(id_attrs):
  """
  Whether there is a _directory_ with that name.
  """

  return fileperms.read_present(id_attrs, stat.S_ISDIR)


class Directory(fileperms.FilePermsMixin, Resource):
  """
  A directory in the filesystem.
  """

  def expand_into(self, rg):
    # Had to rename it to avoid a clash.
    return self.fp_expand_into(rg)

  def create(self):
    path = self.id_attrs['path']
    # Will raise if there is a non-dir in the way.
    os.mkdir(path)

  def update(self):
    # We don't have wanted_attrs beyond perms.
    pass

  def delete(self):
    os.rmdir(path)

def register():
  restype = ResourceType('Directory', Directory,
      id_type={
        'path': AttrType(
          pytype=str,
          valid_condition=fileperms.is_valid_path),
        },
      state_type={
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        'mode': AttrType(
          default_value='0700',
          reader=fileperms.read_mode,
          valid_condition=fileperms.is_valid_mode,
          pytype=str),
        'owner': AttrType(
          none_allowed=True,
          reader=fileperms.read_owner,
          # Commenting due to users created after validation
          #valid_condition=fileperms.is_valid_username,
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


