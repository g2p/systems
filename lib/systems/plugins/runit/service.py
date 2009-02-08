# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


class Service(EResource):
  """
  A directory for a single service.
  """

  def expand_into(self, rg):
    loc_ref = self.id_attrs['location']
    run_file_path = loc_ref.unref.id_attrs['path'] + '/run'
    contents = self.wanted_attrs['contents']
    present = self.wanted_attrs['present']
    rg.add_resource(resource('PlainFile',
        path=run_file_path,
        mode='0755',
        contents=contents,
        present=present,
        ),
      depends=(loc_ref, ))


def register():
  restype = ResourceType('Service', Service,
    id_type={
      'location': RefAttrType(
        rtype='Directory'),
      },
    state_type={
      'present': AttrType(
        default_value=True,
        pytype=bool),
      'contents': AttrType(
        pytype=str),
      })
  get_registry().resource_types.register(restype)


