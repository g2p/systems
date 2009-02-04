# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.transitions.file.directory import Directory


class Rails(Resource):
  """
  A rails application.
  """

  def expand_into(self, rg):
    location = self.id_attrs['location']
    if not location.wanted_attrs['present']:
      raise ValueError

    pkg = rg.add_resource(resource('AptitudePackage', name='rails'))


def register():
  restype = ResourceType('Rails', Rails,
    id_type={
      'location': AttrType(
        pytype=Directory),
      },
    state_type={
      })
  Registry.get_singleton().resource_types.register(restype)


