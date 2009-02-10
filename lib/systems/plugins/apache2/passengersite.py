# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource
from systems.util.templates import build_and_render


class PassengerSite(EResource):
  """
  A rails app running using passenger.
  """

  def expand_into(self, rg):
    name = self.id_attrs['name']
    present = self.wanted_attrs['present']
    enabled = self.wanted_attrs['enabled']
    hostname = self.wanted_attrs['hostname']
    port = self.wanted_attrs['port']
    rails_dir = self.wanted_attrs['rails_dir']

    rails_pub_path = rails_dir.id_attrs['path'] + '/public'
    contents = build_and_render('''
DocumentRoot {{ rails_pub_path }}
RailsBaseUri /
''',
      rails_pub_path=rails_pub_path,
      ).encode('utf8')

    fastthread = rg.add_resource(resource('RubyGem',
        name='fastthread', version='1.0.1'))
    worker_mpm = rg.add_resource(resource('AptitudePackage',
        name='apache2-mpm-worker'))
    rg.add_resource(resource('A2Site',
        name=name,
        present=present,
        enabled=enabled,
        hostname=hostname,
        port=port,
        contents=contents,
        ),
      depends=[fastthread, worker_mpm],
      )


def register():
  restype = ResourceType('PassengerSite', PassengerSite,
    id_type={
      'name': AttrType(
        pytype=str),
      },
    state_type={
      'present': AttrType(
        default_value=True,
        pytype=bool),
      'enabled': AttrType(
        default_value=True,
        pytype=bool),
      'hostname': AttrType(
        # I suppose that's secure by default; if not, maybe 127.0.0.1.
        default_value='localhost',
        pytype=str),
      'port': AttrType(
        default_value=80,
        pytype=int),
      'rails_dir': RefAttrType(
        rtype='Directory'),
      })
  get_registry().resource_types.register(restype)


