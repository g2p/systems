# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.registry import Registry
from systems.context import global_context
from systems.realizable import TypedRealizable

__all__ = ('Resource', 'ensure_resource', 'ref_resource', )


class Resource(TypedRealizable):
  """
  A resource, representing a state of some part of the system.

  A resource has an identity that is common to all possible states.
  """

  pass


def ensure_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().resource_types.lookup(typename)
  return t.ensure(valdict=kwargs, context=context, extra_deps=depends)

def ref_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().resource_types.lookup(typename)
  return t.ensure_ref(valdict=kwargs, context=context, extra_deps=depends)


