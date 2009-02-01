# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from itertools import ifilter

import networkx as NX

from systems.typesystem import Resource, Transition, ResourceRef
from systems.registry import Registry

__all__ = ('Context', 'global_context', )


class SentinelNode(object):
  pass

class DepsGraph(object):
  """
  A dependency graph.

  Invariant: directed, acyclic.
  Abstract base class; does not support adding nodes.
  """

  def __init__(self):
    self._graph = NX.DiGraph()
    self._first = SentinelNode()
    self._last = SentinelNode()

  def add_dependency(self, node0, node1):
    # Requiring nodes to be already added ensures type safety
    if not self._graph.has_node(node0):
      raise KeyError(node0)
    if not self._graph.has_node(node1):
      raise KeyError(node1)
    if node0 == node1:
      # Disallow self-loops to keep acyclic invariant.
      # Also they don't make sense.
      raise ValueError
    self._graph.add_edge(node0, node1)
    # Expensive check I guess.
    if not NX.is_directed_acyclic_graph(self._graph):
      self._graph.remove_edge(node0, node1)
      #XXX NX doesn't have a 1-line method for listing those cycles
      raise ValueError('Dependency graph has cycles')

  def _add_node(self, node):
    self._graph.add_node(node)
    self._graph.add_edge(self._first, node)
    self._graph.add_edge(node, self._last)

  def nodes_iter(self):
    return ifilter(
        lambda n: not isinstance(n, SentinelNode),
        self._graph.nodes_iter())

  def connected(self, n0, n1):
    if NX.shortest_path(self.__graph, n0, n1) \
        or NX.shortest_path(self.__graph, n1, n0):
      return True
    return False

  def topological_sort(self):
    return [n for n in NX.topological_sort(self._graph)
        if not isinstance(n, SentinelNode)]


class TransitionGraph(DepsGraph):
  def add_transition(self, transition):
    if not isinstance(transition, Transition):
      raise TypeError(transition, Transition)
    self._add_node(transition)

  def merge_transitions(self, transition_graph, predecessors):
    if not isinstance(transition_graph, TransitionGraph):
      raise TypeError
    # Do not skip sentinels.
    for n in transition_graph._graph.nodes_iter():
      self._add_node(n)
    for (n0, n1) in transition_graph._graph.edges_iter():
      self.add_dependency(n0, n1)
    for n in predecessors:
      self.add_dependency(n, transition_graph._first)
    return transition_graph._last


class ResourceGraph(DepsGraph):
  def __init__(self):
    super(ResourceGraph, self).__init__()
    self.__dict = {}

  def add_resource(self, resource):
    if not isinstance(resource, Resource):
      raise TypeError(resource, Resource)
    if resource.id_attrs in self.__dict:
      raise RuntimeError
    self._add_node(resource)
    self.__dict[resource.id_attrs] = resource

  def replace_resources(self, r0s, r1):
    """
    Replace an iterable of resources with one resource.

    May break the acyclic invariant, caveat emptor.
    """

    # The invariant is kept iff the r0s don't have paths linking them.
    # For our use case (collectors), we could allow paths provided they are
    # internal to r0s. This introduces self-loops that we would then remove.

    for r0 in r0s:
      if not r0.id_attrs in self.__dict:
        raise KeyError(r0)
    if r1.id_attrs in self.__dict:
      raise RuntimeError
    self.add_resource(r1)
    for r0 in r0s:
      for pred in self._graph.predecessors_iter(r0):
        self._graph.add_edge(pred, r1)
      for succ in self._graph.successors_iter(r0):
        self._graph.add_edge(r1, succ)
      self._graph.delete_node(r0)

    if not NX.is_directed_acyclic_graph(self._graph):
      # Can't undo.
      raise ValueError('Dependency graph has cycles')


class Context(object):
  """
  A graph of realizables linked by dependencies.
  """

  def __init__(self):
    self.__transitions = TransitionGraph()
    self.__resources = ResourceGraph()
    self.__state = 'init'

  def require_state(self, state):
    """
    Raise an exception if we are not in the required state.
    """

    if self.__state != state:
      raise RuntimeError(u'Context state should be «%s»' % state)

  def ensure_resource(self, r):
    self.require_state('init')

    self.__resources.add_resource(r)

  def ensure_transition(self, t):
    self.require_state('init')

    self.__transitions.add_transition(t)

  def ensure_frozen(self):
    """
    Build the finished dependency graph.

    Resolve references, merge identical realizables, collect what can be.
    """

    if self.__state == 'frozen':
      return
    self.require_state('init')
    self._resolve_references()
    self._collect()
    self._extra_depends()
    self._transitions_from_resources()
    self.__state = 'frozen'

  def _resolve_references(self):
    self.require_state('init')
    # XXX Dropped for now.

  def _collect(self):
    # Collects compatible nodes into merged nodes.
    self.require_state('init')

    def can_merge(part0, part1):
      for n0 in part0:
        for n1 in part1:
          if self.__resources.connected(n0, n1):
            return False
      return True

    def possibly_merge(partition):
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
    for collector in reg.collectors:
      # Pre-partition is made of parts acceptable for the collector.
      pre_partition = collector.partition(
          [r for r in self.__resources.nodes_iter() if collector.filter(r)])
      for part in pre_partition:
        # Collector parts are split again, the sub-parts are merged
        # when dependencies allow.
        # Not a particularly efficient algorithm, just simple.
        # Gives one solution among many possibilities.
        partition = set(frozenset((r, ))
            for r in part
            for part in pre_partition)
        while possibly_merge(partition):
          pass

        # Let the collector handle the rest
        for part in partition:
          if len(part) <= 1:
            continue
          merged = collector.collect(part)
          self.__resources.replace_resources(part, merged)

  def _extra_depends(self):
    for r in self.__resources.nodes_iter():
      r.place_extra_deps(self.__resources)

  def _transitions_from_resources(self):
    # Map resource ids to transition contexts.
    lasts = {}
    for r in self.__resources.topological_sort():
      tg = TransitionGraph()
      r.place_transitions(tg)
      predecessors = [lasts[r0.id_attrs]
          for r0 in self.__resources._graph.predecessors_iter(r)
          if not isinstance(r0, SentinelNode)]
      last = self.__transitions.merge_transitions(tg, predecessors)
      lasts[r.id_attrs] = last

  def realize(self):
    """
    Realize all realizables and transitions in dependency order.
    """

    self.ensure_frozen()
    for t in self.__transitions.topological_sort():
      t.realize()


__global_context = None
def global_context():
  """
  The global instance.
  """

  global __global_context
  if __global_context is None:
    __global_context = Context()
  return __global_context

