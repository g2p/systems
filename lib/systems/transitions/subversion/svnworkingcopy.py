# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs
from systems.transitions.file.directory import Directory


class SvnWorkingCopy(Resource):
  """
  A working copy checked out from a subversion repository.

  This working copy overwrites any local modifications.
  The owner for files and .svn are the same
  as the owner of the desired location.
  """

  def get_extra_deps(self):
    location = self.id_attrs['location']
    # An alternative to valid_condition
    if not location.wanted_attrs['present']:
      raise ValueError
    return (resource('AptitudePackage', name='subversion'), location)

  def place_transitions(self, tg):
    repo_url = self.wanted_attrs['url']
    loc = self.id_attrs['location']
    path = loc.id_attrs['path']
    owner = loc.wanted_attrs['owner']
    co = transition('Command',
        username=owner,
        cmdline=['/usr/bin/svn', 'checkout', '--non-interactive', '--force',
          '--', repo_url, path, ])
    up = transition('Command',
        username=owner,
        cmdline=['/usr/bin/svn', 'update', '--non-interactive', '--force',
          '--', path, ])
    tg.add_transition(co)
    tg.add_transition(up)
    tg.add_transition_dependency(co, up)


def register():
  restype = ResourceType('SvnWorkingCopy', SvnWorkingCopy,
    id_type={
      'location': AttrType(
        pytype=Directory),
      },
    state_type={
      'url': AttrType(
        pytype=str),
      })
  Registry.get_singleton().resource_types.register(restype)


