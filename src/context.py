
import networkx as NX

__all__ = ('Context', 'global_context', )


class Context(object):
  """
  A graph of resources linked by dependencies.
  """

  def __init__(self):
    self.__deps_graph = NX.DiGraph()
    self.__res_set = {}
    self.__ref_set = {}
    self.__state = 'init'

  def check_state(self, value):
    if self.__state != value:
      raise RuntimeError('Context state should be %s' % value)

  def ensure_resource(self, res, extra_deps, is_reference):
    """
    Add a resource or resource reference to be managed by this graph.
    """

    from resource import ResourceRef

    self.check_state('init')
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
    self.add_dependency(res, extra_deps)
    return res

  def add_dependency(self, resource, dependencies):
    """
    Adds a dependency relationship, from dependencies to a target resource.

    resource is the resource to add dependencies to,
    dependencies is an iterable of resources.

    resource and dependencies must already have been added
    with add_resource.

    References can be used instead of resources.
    """

    self.check_state('init')
    if not (resource.identity in self.__res_set
        or resource.identity in self.__ref_set):
      raise RuntimeError('First add the resource')
    for dep in dependencies:
      if not (dep.identity in self.__res_set or dep.identity in self.__ref_set):
        raise RuntimeError('First add the resource')
      self.__deps_graph.add_edge(dep, resource)

  def ensure_frozen(self):
    """
    Resolve references, merge identical resources, prepare dependencies.
    """

    if self.__state == 'frozen':
      return
    self.check_state('init')

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
    Realize all resources, respecting dependency order.
    """

    self.ensure_frozen()
    if not NX.is_directed_acyclic_graph(self.__deps_graph):
      #XXX NX doesn't have a 1-line method for listing those cycles
      raise ValueError('Dependency graph has cycles')
    for r in NX.topological_sort(self.__deps_graph):
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

# vim: set sw=2 ts=2 et :
