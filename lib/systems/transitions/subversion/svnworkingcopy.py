# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource


class SvnWorkingCopy(Resource):
  """
  A working copy checked out from a subversion repository.

  This working copy overwrites any local modifications.
  The owner for files and .svn are the same
  as the owner of the desired location.
  """

  def expand_into(self, rg):
    location = self.id_attrs['location']
    # An alternative to valid_condition
    if not location.wanted_attrs['present']:
      raise ValueError

    pkg = rg.add_resource(resource('AptitudePackage', name='subversion'))

    repo_url = self.wanted_attrs['url']
    path = location.id_attrs['path']
    owner = location.wanted_attrs['owner']

    co = transition('Command',
        username=owner,
        cmdline=['/usr/bin/svn', 'checkout', '--non-interactive', '--force',
          '--', repo_url, path, ])
    up = transition('Command',
        username=owner,
        cmdline=['/usr/bin/svn', 'update', '--non-interactive', '--force',
          '--', path, ])

    rg.add_transition(co)
    rg.add_transition(up)
    rg.add_dependency(pkg, co)
    rg.add_dependency(self.passed_by_ref['location'], co)
    rg.add_dependency(co, up)


def register():
  restype = ResourceType('SvnWorkingCopy', SvnWorkingCopy,
    id_type={
      'location': AttrType(
        rtype='Directory'),
      },
    state_type={
      'url': AttrType(
        pytype=str),
      })
  Registry.get_singleton().resource_types.register(restype)


