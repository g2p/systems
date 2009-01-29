# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import networkx as NX

from systems.typesystem import InstanceBase, InstanceRef
from systems.realizable import Realizable, EmptyRealizable
from systems.registry import Registry

__all__ = ('Context', 'global_context', )


class Context(Realizable):
  """
  A graph of realizables linked by dependencies.
  """

  def __init__(self):
    self.__deps_graph = NX.DiGraph()
    # Realizables, references and anons are managed separately,
    # until the graph is frozen.
    self.__rea_set = {}
    self.__ref_set = {}
    self.__anon_set = set()
    self.__state = 'init'
    self.__first = EmptyRealizable()
    self.__last = EmptyRealizable()
    self.__deps_graph.add_edge(self.__first, self.__last)
    self.__anon_set.add(self.__first)
    self.__anon_set.add(self.__last)

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

    if isinstance(r, InstanceRef):
      self.__ref_set[r.identity] = r
    elif isinstance(r, InstanceBase):
      set = self.__rea_set
      if id in set:
        res0 = set[id]
        if res0.attributes != r.attributes:
          raise RuntimeError(
              u'Realizable instance conflict: «%s» and «%s»'% (res0, r))
      self.__rea_set[r.identity] = r
    elif isinstance(r, EmptyRealizable):
      self.__anon_set.add(r)
    else:
      raise TypeError('Neither an instance nor a reference: «%s»' % r)

    self.__deps_graph.add_node(r)

    for extra_dep in extra_deps:
      self.ensure_realizable(extra_dep, ())
      self.add_dependency(r, extra_dep)
    self.add_dependency(r, self.__first)
    self.add_dependency(self.__last, r)
    return r

  def require_valid_realizable(self, r):
    if isinstance(r, InstanceRef):
      if r.identity in self.__ref_set:
        return
    elif isinstance(r, InstanceBase):
      if r.identity in self.__rea_set:
        return
    elif isinstance(r, EmptyRealizable):
      if r in self.__anon_set:
        return
    else:
      raise TypeError
    raise RuntimeError('No such realizable in contest: «%s»' % r)

  def add_dependency(self, dependent, dependency):
    """
    Add a dependency relationship (realization ordering constraint).

    realizable and dependency are realizables
    (resources, transitions or references),
    and must already have been added with add_realizable.
    """

    self.require_state('init')
    self.require_valid_realizable(dependent)
    self.require_valid_realizable(dependency)
    self.__deps_graph.add_edge(dependency, dependent)

  def ensure_frozen(self):
    """
    Build the finished dependency graph.

    Resolve references, merge identical realizables, collect what can be.
    """

    if self.__state == 'frozen':
      return
    self.require_state('init')

    # Resolve references, merge identical realizables
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

    if not NX.is_directed_acyclic_graph(self.__deps_graph):
      #XXX NX doesn't have a 1-line method for listing those cycles
      raise ValueError('Dependency graph has cycles')

    # The rest of the method collects compatible nodes into merged nodes.

    def can_merge(part0, part1):
      for n0 in part0:
        for n1 in part1:
          if NX.shortest_path(self.__deps_graph, n0, n1) \
              or NX.shortest_path(self.__deps_graph, n1, n0):
                return False
      return True
    def may_merge(partition):
      # Merge once if possible. Return true if did merge.
      e = dict(enumerate(partition))
      n = len(partition)
      # Loop over the triangle of unordered pairs
      for i in xrange(n):
        for j in xrange(i + 1, n):
          part0, part1 = e[i], e[j]
          if can_merge(part0, part1):
            partition.add(part0.union(part1))
            partition.remove(part0)
            partition.remove(part1)
            return True
      return False
    reg = Registry.get_singleton()
    for collector_name in reg.collectors:
      collector = reg.collectors.lookup(collector_name)
      partition = set(frozenset((r, ))
          for r in self.__deps_graph
          if collector.collect_filter(r))
      # Not a particularly efficient algorithm, just simple.
      # Also there are multiple solutions.
      while may_merge(partition):
        pass
      for part in partition:
        if len(part) == 1:
          continue
        merged = collector.collect(part)
        self.__deps_graph.add_node(merged)
        for n in part:
          for pred in self.__deps_graph.predecessors_iter(n):
            self.__deps_graph.add_edge(pred, merged)
          for succ in self.__deps_graph.successors_iter(n):
            self.__deps_graph.add_edge(merged, succ)
          self.__deps_graph.delete_node(n)

    # Check we didn't introduce a cycle.
    assert NX.is_directed_acyclic_graph(self.__deps_graph)
    self.__state = 'frozen'

  def realize(self):
    """
    Realize all realizables and transitions in dependency order.
    """

    self.ensure_frozen()
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

