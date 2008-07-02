
import networkx as NX

__all__ = ('ResourceGraph', 'global_graph', )


class ResourceGraph(object):
  """
  A graph of resources linked by dependencies.
  """

  def __init__(self):
    self.__deps_graph = NX.DiGraph()
    self.__state = 'init'

  def check_state(self, value):
    if self.__state != value:
      raise RuntimeError('ResourceGraph state should be %s' % value)

  def add_resource(self, resource):
    """
    Add a resource to be managed by this graph.
    """

    self.check_state('init')
    self.__deps_graph.add_node(resource)

  def add_dependency(self, resource, dependencies):
    """
    Add dependencies to a target resource.

    resource is the resource to add dependencies to,
    dependencies is an iterable of resources.
    
    resource and dependencies must already have been added
    with add_resource.
    """

    self.check_state('init')
    for dep in dependencies:
      self.__deps_graph.add_edge(dep, resource)

  def ensure_frozen(self):
    if self.__state == 'frozen':
      return
    self.check_state('init')
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

__global_graph = None
def global_graph():
  """
  The global resource graph instance.
  """

  global __global_graph
  if __global_graph is None:
    __global_graph = ResourceGraph()
  return __global_graph

# vim: set sw=2 ts=2 et :
