# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import networkx as NX

from systems.typesystem import InstanceRef

__all__ = ('Context', 'global_context', )


class Context(object):
  """
  A graph of realizables linked by dependencies.
  """

  def __init__(self):
    self.__deps_graph = NX.DiGraph()
    # Realizables and references are managed separately,
    # until the graph is frozen.
    self.__rea_set = {}
    self.__ref_set = {}
    self.__state = 'init'

  def require_state(self, state):
    """
    Raise an exception if we are not in the required state.
    """

    if self.__state != state:
      raise RuntimeError(u'Context state should be «%s»' % state)

  def ensure_realizable(self, r, extra_deps):
    """
    Add a realizable or realizable reference to be managed by this graph.
    """

    self.require_state('init')

    is_reference = isinstance(r, InstanceRef)
    id = r.identity

    if is_reference:
      set = self.__ref_set
    else:
      set = self.__rea_set

    if id in set:
      res0 = set[id]
      if res0.attributes == r.attributes:
        return res0
      else:
        raise RuntimeError(u'Realizable conflict: «%s» and «%s»'% (res0, r))

    set[id] = r
    self.__deps_graph.add_node(r)

    for extra_dep in extra_deps:
      self.ensure_realizable(extra_dep, ())
      self.add_dependency(r, extra_dep)
    return r

  def add_dependency(self, dependent, dependency):
    """
    Add a dependency relationship (realization ordering constraint).

    realizable and dependency are realizables
    (resources, transitions or references),
    and must already have been added with add_realizable.
    """

    self.require_state('init')
    if not (dependent.identity in self.__rea_set
        or dependent.identity in self.__ref_set):
      raise RuntimeError('First add the dependent realizable')
    if not (dependency.identity in self.__rea_set
        or dependency.identity in self.__ref_set):
      raise RuntimeError('First add the dependency realizable')
    self.__deps_graph.add_edge(dependency, dependent)

  def ensure_frozen(self):
    """
    Resolve references, merge identical realizables, prepare dependencies.
    """

    if self.__state == 'frozen':
      return
    self.require_state('init')

    for ref in self.__ref_set.itervalues():
      id = ref.identity
      if not id in self.__rea_set:
        raise RuntimeError(u'Unresolved realizable reference, id «%s»' % id)
      rea = self.__rea_set[id]
      # Replace edges to ref with edges to rea.
      for pred in self.__deps_graph.predecessors_iter(ref):
        self.__deps_graph.add_edge(pred, rea)
      for succ in self.__deps_graph.successors_iter(ref):
        self.__deps_graph.add_edge(rea, succ)
      self.__deps_graph.delete_node(ref)
    del self.__ref_set
    del self.__rea_set

    self.__state = 'frozen'

  def realize(self):
    """
    Realize all realizables and transitions in dependency order.
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
  The global instance.
  """

  global __global_context
  if __global_context is None:
    __global_context = Context()
  return __global_context

