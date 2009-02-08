# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


class SvDir(EResource):
  """
  A directory grouping several services.
  """

  def expand_into(self, rg):
    loc_ref = self.id_attrs['location']


def register():
  restype = ResourceType('SvDir', SvDir,
    id_type={
      'location': RefAttrType(
        rtype='Directory'),
      },
    state_type={
      'present': AttrType(
        default_value=True,
        pytype=bool),
      })
  get_registry().resource_types.register(restype)


