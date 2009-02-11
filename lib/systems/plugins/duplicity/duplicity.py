# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, ResourceType, EResource
from systems.util.templates import build_and_render


class Duplicity(EResource):
  """
  Backups with duplicity.
  """

  def expand_into(self, rg):
    # XXX key mngmt
    source_path = self.id_attrs['source'].id_attrs['path']
    dest_url = self.id_attrs['dest']
    pkg = rg.add_resource(resource('AptitudePackage',
        name='duplicity',
        ))
    cmd = rg.add_transition(transition('Command',
        cmdline=['/usr/bin/duplicity', source_path, dest_url ]
        ),
      depends=[pkg])


def register():
  restype = ResourceType('Duplicity', Duplicity,
    id_type={
      'source': AttrType(
        rtype='Directory'),
      'dest': AttrType(
        pytype=str),
      },
    state_type={
      })
  get_registry().resource_types.register(restype)


