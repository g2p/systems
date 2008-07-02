
import networkx as NX

__all__ = ('ResourceGraph', 'global_graph', )


class ResourceGraph(object):
  """
  A graph of resources linked by dependencies.
  """

  def __init__(self):
    self.__deps_graph = NX.Graph()

  def add_resource(self, resource):
    """
    Add a resource to be managed by this graph.
    """

    self.__deps_graph.add_node(resource)

  def add_dependency(self, resource, dependencies):
    """
    Add dependencies to a target resource.


    resource is the resource to add dependencies to,
    dependencies is an iterable of resources.
    
    resource and dependencies must already have been added
    with add_resource.
    """

    self.__deps_graph.add_edge(resource, dependencies)

__global_graph = None
def global_graph():
  """
  The global resource graph instance.
  """

  global __global_graph
  if not __global_graph:
    __global_graph = ResourceGraph()
  return __global_graph

# vim: set sw=2 ts=2 et :
