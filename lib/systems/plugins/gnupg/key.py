# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, ResourceType, EResource
from systems.util.templates import build_and_render


class Key(EResource):
  """
  A GPG key, comprised of public and private parts.
  """

  def expand_into(self, rg):
    name = self.id_attrs['name']
    enabled = self.wanted_attrs['enabled']
    apache2 = rg.add_to_top(resource('AptitudePackage',
        name='apache2.2-common',
        ))
    cmd = '/usr/sbin/a2%smod' % { True: 'en', False: 'dis', }[enabled]
    endis = rg.add_transition(transition('Command',
        cmdline=[cmd, name, ]
        ),
      depends=[apache2])
    # XXX invoke-rc.d apache2 force-reload on any state change.


def register():
  restype = ResourceType('Key', Key,
    id_type={
      'name': AttrType(
        pytype=str),
      },
    state_type={
      'enabled': AttrType(
        default_value=True,
        pytype=bool),
      })
  get_registry().resource_types.register(restype)


