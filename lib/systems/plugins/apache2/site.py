# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, ResourceType, EResource
from systems.util.templates import build_and_render


class Site(EResource):
  """
  An apache2 site.
  """

  def expand_into(self, rg):
    name = self.id_attrs['name']
    present = self.wanted_attrs['present']
    enabled = self.wanted_attrs['enabled']
    hostname = self.wanted_attrs['hostname']
    port = self.wanted_attrs['port']
    contents = self.wanted_attrs['contents']
    if not present and enabled:
      raise ValueError(present, enabled)

    fcontents = build_and_render('''
NameVirtualHost {{ hostname }}:{{ port }}
<VirtualHost {{ hostname }}:{{ port }}>
{{ contents }}
</VirtualHost>
''',
      contents=contents,
      hostname=hostname,
      port=port).encode('utf8')
    apache2 = rg.add_resource(resource('AptitudePackage',
        name='apache2.2-common',
        ))
    site_file = rg.add_resource(resource('PlainFile',
        path='/etc/apache2/sites-available/' + name,
        contents=fcontents,
        present=present,
        mode='0644',
        ),
      depends=[apache2])
    cmd = '/usr/sbin/a2%ssite' % { True: 'en', False: 'dis', }[enabled]
    endis = rg.add_transition(transition('Command',
        cmdline=[cmd, name, ]
        ),
      depends=[site_file])
    # XXX invoke-rc.d apache2 reload on any state change.


def register():
  restype = ResourceType('Site', Site,
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
      'contents': AttrType(
        pytype=str),
      })
  get_registry().resource_types.register(restype)


