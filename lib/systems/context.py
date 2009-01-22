# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import networkx as NX
from systems.decorators import propget, memoized

__all__ = ('Context', 'global_context', )


class Context(object):
  """
  A graph of resources linked by dependencies.
  """

  def __init__(self):
    self.__deps_graph = NX.XDiGraph()
    self.__res_set = {}
    self.__ref_set = {}
    self.__trans_set = set()
    self.__state = 'init'

  @propget
  @memoized
  def first_sentinel(self):
    # XXX Should use a singleton ResourceType.
    # Must relax the constraints on naming/identifying attrs to do that.
    from systems.resouce import DummyResource
    return DummyResource()

  @propget
  @memoized
  def last_sentinel(self):
    from systems.resouce import DummyResource
    return DummyResource()

  def require_state(self, state):
    """
    Raise an exception if we are not in the required state.
    """

    if self.__state != state:
      raise RuntimeError('Context state should be %s' % state)

  def ensure_resource(self, res, extra_deps, is_reference):
    """
    Add a resource or resource reference to be managed by this graph.
    """

    from systems.resource import ResourceRef

    self.require_state('init')
    id = res.identity
    if is_reference:
      set = self.__ref_set
    else:
      set = self.__res_set

    if id in set:
      res0 = set[id]
      if res0.attributes == res.attributes:
        return res0
      else:
        raise RuntimeError('Resource conflict: %s, %s'% (res0, res))

    set[id] = res
    self.__deps_graph.add_node(res)

    for d in extra_deps:
      self.ensure_resource(d, (), isinstance(d, ResourceRef))
    for extra_dep in extra_deps:
      self.add_dependency(res, extra_dep)
    return res

  def add_dependency(self, resource, dependency, transition=None):
    """
    Add a dependency relationship (realization ordering constraint).

    resource and dependency are resources and references,
    and must already have been added with add_resource.

    transition, if passed, is a transition to run between the
    realisation of resource and dependency.
    """

    self.require_state('init')
    if not (resource.identity in self.__res_set
        or resource.identity in self.__ref_set):
      raise RuntimeError('First add the resource')
    if not (dependency.identity in self.__res_set
        or dependency.identity in self.__ref_set):
      raise RuntimeError('First add the dependent resource')
    self.__deps_graph.add_edge(dependency, resource, transition)

  def ensure_frozen(self):
    """
    Resolve references, merge identical resources, prepare dependencies.
    """

    if self.__state == 'frozen':
      return
    self.require_state('init')

    for ref in self.__ref_set.itervalues():
      id = ref.identity
      if not id in self.__res_set:
        raise RuntimeError('Unresolved resource reference, id %s' % id)
      res = self.__res_set[id]
      for pred in self.__deps_graph.predecessors_iter(ref):
        self.__deps_graph.add_edge(pred, res)
      for succ in self.__deps_graph.successors_iter(ref):
        self.__deps_graph.add_edge(res, succ)
      self.__deps_graph.delete_node(ref)
    del self.__ref_set
    del self.__res_set

    for r in self.__deps_graph.nodes_iter():
      r.prepare_deps()

    self.__state = 'frozen'

  def realize(self):
    """
    Realize all resources and transitions in dependency order.
    """

    self.ensure_frozen()
    if not NX.is_directed_acyclic_graph(self.__deps_graph):
      #XXX NX doesn't have a 1-line method for listing those cycles
      raise ValueError('Dependency graph has cycles')
    for r in NX.topological_sort(self.__deps_graph):
      for pred in self.__deps_graph.predecessors(r):
        transition = self.__deps_graph.get_edge(pred, r)
        if transition is not None:
          transition.realize()
      r.realize()


__global_context = None
def global_context():
  """
  The global resource graph instance.
  """

  global __global_context
  if __global_context is None:
    __global_context = Context()
  return __global_context

