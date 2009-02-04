# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from rails import Rails

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.transitions.file.directory import Directory


class Redmine(Resource):
  """
  A redmine instance.
  """

  def expand_into(self, rg):
    rails = self.id_attrs['rails']
    loc = rails.id_attrs['location']
    svn_branch = self.wanted_attrs['svn_branch']
    wc = rg.add_resource(resource('SvnWorkingCopy',
      location=loc,
      url=svn_branch))
    rails = rg.add_resource(rails)
    rg.add_dependency(wc, rails)


def register():
  restype = ResourceType('Redmine', Redmine,
    id_type={
      'rails': AttrType(
        pytype=Rails),
      },
    state_type={
      'svn_branch': AttrType(
        default_value='http://redmine.rubyforge.org/svn/branches/0.8-stable/',
        pytype=str),
      })
  Registry.get_singleton().resource_types.register(restype)


