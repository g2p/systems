# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


class Service(EResource):
  """
  A directory for a single service.
  """

  def expand_into(self, rg):
    loc_ref = self.id_attrs['location']
    loc_path = loc_ref.id_attrs['path']
    run_file_path = loc_path + '/run'
    contents = self.wanted_attrs['contents']
    present = self.wanted_attrs['present']
    status = self.wanted_attrs['status']
    if not present and status != 'down':
      raise ValueError(present, status)

    down_file_present = present and status == 'down'
    down_file = rg.add_resource(resource('PlainFile',
        path=loc_path+'/down',
        mode='0644',
        present=down_file_present,
        ),
      depends=(loc_ref, ))
    run_file = rg.add_resource(resource('PlainFile',
        path=run_file_path,
        mode='0755',
        present=present,
        contents=contents,
        ),
      depends=(down_file, ))
    if present:
      # We have no guarantee there is a runsv for us,
      # be lax with exit codes.
      cmd = {'up': 'start', 'down': 'force-shutdown', }[status]
      set_state = rg.add_transition(transition('Command',
          cmdline=['/usr/bin/sv', cmd, loc_path],
          expected_retcodes=(0, 1, ),
          ),
        depends=(run_file, ))


def register():
  restype = ResourceType('Service', Service,
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
      'contents': AttrType(
        pytype=str),
      })
  get_registry().resource_types.register(restype)


