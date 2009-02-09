# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource
from systems.util.templates import build_and_render


class DirService(EResource):
  """
  A service that runs runsvdir for a target service dir.
  """

  def expand_into(self, rg):
    loc_ref = self.id_attrs['location']
    present = self.wanted_attrs['present']
    status = self.wanted_attrs['status']
    target_dir_ref = self.wanted_attrs['target_dir']
    target_path = target_dir_ref.id_attrs['path']
    contents = build_and_render('''#!/bin/sh
exec 2>&1
exec runsvdir {{ target_path }}
''', target_path=target_path).encode('utf8')
    rg.add_resource(resource('Service',
        location=loc_ref,
        present=present,
        status=status,
        contents=contents,
        ),
      depends=(target_dir_ref, ))


def register():
  restype = ResourceType('DirService', DirService,
    id_type={
      'location': RefAttrType(
        rtype='Directory'),
      },
    state_type={
      'status': AttrType(
        default_value='up',
        valid_values=('up', 'down', ),
        pytype=str),
      'present': AttrType(
        default_value=True,
        pytype=bool),
      'target_dir': RefAttrType(
        rtype='Directory'),
      })
  get_registry().resource_types.register(restype)


