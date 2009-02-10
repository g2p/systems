# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


class SvnWorkingCopy(EResource):
  """
  A working copy checked out from a subversion repository.

  This working copy overwrites any local modifications.
  The owner for files and .svn are the same
  as the owner of the desired location.
  """

  def expand_into(self, rg):
    loc_ref = self.id_attrs['location']
    # An alternative to valid_condition
    if not loc_ref.wanted_attrs['present']:
      raise ValueError

    pkg_ref = rg.add_to_top(resource('AptitudePackage', name='subversion'))

    repo_url = self.wanted_attrs['url']
    path = loc_ref.id_attrs['path']
    owner = loc_ref.wanted_attrs['owner']

    co = rg.add_transition(transition('Command',
        username=owner,
        cmdline=['/usr/bin/svn', 'checkout', '--non-interactive', '--force',
          '--', repo_url, path, ]),
      depends=(pkg_ref, loc_ref, ))
    up = rg.add_transition(transition('Command',
        username=owner,
        cmdline=['/usr/bin/svn', 'update', '--non-interactive', '--force',
          '--', path, ]),
      depends=(co, ))


def register():
  restype = ResourceType('SvnWorkingCopy', SvnWorkingCopy,
    id_type={
      'location': RefAttrType(
        rtype='Directory'),
      },
    state_type={
      'url': AttrType(
        pytype=str),
      })
  get_registry().resource_types.register(restype)


