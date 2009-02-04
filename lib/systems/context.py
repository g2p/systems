# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from itertools import ifilter

import networkx as NX

from systems.collector import Aggregate, CollectibleResource
from systems.registry import Registry
from systems.typesystem import Resource, Transition, ResourceRef

__all__ = ('Context', 'global_context', )


class SentinelNode(object):
  pass

class CheckPointSentinel(SentinelNode):
  pass

class ResourceSentinel(SentinelNode):
  def __init__(self, res):
    self._res = res

class BeforeResourceSentinel(ResourceSentinel):
  pass

class AfterResourceSentinel(ResourceSentinel):
  pass

class GraphFirstSentinel(SentinelNode):
  pass

class GraphLastSentinel(SentinelNode):
  pass

class ResInGraph(object):
  def __init__(self, res, before, after):
    self._res = res
    self._before = before
    self._after = after
    self._expanded = False

class ResourceGraph(object):
  """
  A graph of resources and transitions linked by dependencies.

  Resources are positioned as two sentinels in the transition graph.

  Invariant: directed, acyclic.
  """

  def __init__(self):
    self._graph = NX.DiGraph()
    self._first = GraphFirstSentinel()
    self._last = GraphLastSentinel()
    self._graph.add_edge(self._first, self._last)
    # Stores ResInGraph entries.
    self.__dict = {}

  def _add_transition_dependency(self, node0, node1):
    if not isinstance(node0, (Transition, SentinelNode)):
      raise TypeError(node0, (Transition, SentinelNode))
    if not isinstance(node1, (Transition, SentinelNode)):
      raise TypeError(node1, (Transition, SentinelNode))
    if not self._graph.has_node(node0):
      raise KeyError(node0)
    if not self._graph.has_node(node1):
      raise KeyError(node1)
    if self._graph.has_edge(node0, node1):
      return False
    if node0 == node1:
      # Disallow self-loops to keep acyclic invariant.
      # Also they don't make sense.
      raise ValueError
    self._graph.add_edge(node0, node1)
    # Expensive check I guess.
    if not NX.is_directed_acyclic_graph(self._graph):
      # Re-establish invariant.
      self._graph.delete_edge(node0, node1)
      # XXX NX doesn't have a 1-line method for listing those cycles
      raise ValueError('Dependency graph has cycles', node0, node1)
    return True

  def _add_node(self, node, *depends):
    self._graph.add_node(node)
    self._graph.add_edge(self._first, node)
    self._graph.add_edge(node, self._last)
    r = node
    for dep in depends:
      self.add_dependency(dep, node)
    return r

  def add_checkpoint(self, *depends):
    return self._add_sentinel(CheckPointSentinel(), *depends)

  def _add_sentinel(self, node, *depends):
    if not isinstance(node, SentinelNode):
      raise TypeError(node, SentinelNode)
    return self._add_node(node, *depends)

  def sorted_transitions(self):
    return [n for n in NX.topological_sort(self._graph)
        if not isinstance(n, SentinelNode)]

  def add_transition(self, transition, *depends):
    if not isinstance(transition, Transition):
      raise TypeError(transition, Transition)
    return self._add_node(transition, *depends)

  def resource_at(self, key):
    return self.__dict[key]._res

  def iter_resources(self):
    for rig in self.__dict.itervalues():
      yield rig._res

  def _iter_expandables(self):
    for rig in self.__dict.itervalues():
      if not rig._expanded:
        yield rig._res

  def iter_expandable_resources(self):
    for res in self._iter_expandables():
      if not isinstance(res, CollectibleResource):
        yield res

  def iter_expandable_aggregates(self):
    for res in self._iter_expandables():
      if isinstance(res, Aggregate):
        yield res

  def has_expandables(self):
    l = [rig for rig in self.__dict.itervalues() if not rig._expanded]
    return bool(l) # Tests for emptiness

  def add_resource(self, resource, *depends):
    """
    Add a resource.

    If an identical resource exists, it is returned.
    """

    if not isinstance(resource, Resource):
      raise TypeError(resource, Resource)
    return self._add_roa_internal(resource, *depends)

  def _add_resource_or_aggregate(self, roa):
    if not isinstance(roa, (Resource, Aggregate)):
      raise TypeError(roa, (Resource, Aggregate))
    return self._add_roa_internal(roa)

  def _add_roa_internal(self, node, *depends):
    if node.identity in self.__dict:
      r2 = self.__dict[node.identity]._res
      if node == r2:
        return r2
      raise RuntimeError(node, r2)
    before = BeforeResourceSentinel(node)
    after = AfterResourceSentinel(node)
    self._add_sentinel(before, *depends)
    self._add_sentinel(after)
    self._add_transition_dependency(before, after)
    self.__dict[node.identity] = ResInGraph(node, before, after)
    return node

  def add_dependency(self, node0, node1):
    if isinstance(node0, (Resource, Aggregate)):
      node0 = self.__dict[node0.identity]._after
    if isinstance(node1, (Resource, Aggregate)):
      node1 = self.__dict[node1.identity]._before
    return self._add_transition_dependency(node0, node1)

  def _is_direct_rconnect(self, r0, r1):
    s0 = self.__dict[r0.identity]._after
    s1 = self.__dict[r1.identity]._before
    # shortest_path is also a test for connectedness.
    return bool(NX.shortest_path(self._graph, s0, s1))

  def resources_connected(self, r0, r1):
    return self._is_direct_rconnect(r0, r1) \
        or self._is_direct_rconnect(r1, r0)

  def collect_resources(self, r0s, r1):
    """
    Replace an iterable of resources with one new resource.

    May break the acyclic invariant, caveat emptor.
    """

    # The invariant is kept iff the r0s don't have paths linking them.
    # For our use case (collectors), we could allow paths provided they are
    # internal to r0s. This introduces self-loops that we would then remove.

    if r1.identity in self.__dict:
      raise ValueError
    for r0 in r0s:
      if not r0.identity in self.__dict:
        raise KeyError(r0)
      if r0.identity == r1.identity:
        raise ValueError(r0)

    r1 = self._add_resource_or_aggregate(r1)
    before1 = self.__dict[r1.identity]._before
    after1 = self.__dict[r1.identity]._after

    for r0 in r0s:
      before0 = self.__dict[r0.identity]._before
      after0 = self.__dict[r0.identity]._after
      for pred in self._graph.predecessors_iter(before0):
        self._graph.add_edge(pred, before1)
      for succ in self._graph.successors_iter(after0):
        self._graph.add_edge(after1, succ)

      self._graph.delete_node(before0)
      self._graph.delete_node(after0)
      del self.__dict[r0.identity]

    if not NX.is_directed_acyclic_graph(self._graph):
      # Can't undo. Invariant will stay broken.
      raise ValueError('Dependency graph has cycles')

  def expand_resource(self, res):
    """
    Replace res by a small resource graph.

    The resource_graph is inserted in the main graph
    between the sentinels that represent the resource.

    """

    if not res.identity in self.__dict:
      raise KeyError(res)
    if self.__dict[res.identity]._expanded:
      raise RuntimeError

    resource_graph = ResourceGraph()
    res.expand_into(resource_graph)

    # Do not skip sentinels.
    for n in resource_graph._graph.nodes_iter():
      self._add_node(n)
    for (n0, n1) in resource_graph._graph.edges_iter():
      self.add_dependency(n0, n1)

    for (id, rig) in resource_graph.__dict.iteritems():
      assert not rig._expanded
      if id in self.__dict:
        # Identification
        rig1 = self.__dict[id]
        for pred in self._graph.predecessors_iter(rig._before):
          self._graph.add_edge(pred, rig1._before)
        for succ in self._graph.successors_iter(rig._after):
          self._graph.add_edge(rig1._after, succ)
        self._graph.delete_node(rig._before)
        self._graph.delete_node(rig._after)
        if not NX.is_directed_acyclic_graph(self._graph):
          raise RuntimeError('Identification broke the invariant')
      else:
        self.__dict[id] = rig

    rig = self.__dict[res.identity]
    # XXX Problematic:
    # A dependency is put before a resource (through another dependency),
    # but the resource also calls up the same dependency internally.
    # The problem is, the dependency appears at both sides
    # of resource._before.
    self.add_dependency(rig._before, resource_graph._first)
    self.add_dependency(resource_graph._last, rig._after)
    # Do not delete; we must still be able to identify
    # to avoid redundant expansion.
    self.__dict[res.identity]._expanded = True


class Context(object):
  """
  A graph of realizables linked by dependencies.
  """

  def __init__(self):
    self.__resources = ResourceGraph()
    self.__state = 'init'

  def require_state(self, state):
    """
    Raise an exception if we are not in the required state.
    """

    if self.__state != state:
      raise RuntimeError(u'Context state should be «%s»' % state)

  def ensure_resource(self, r):
    """
    Add a resource to be realized.

    If an identical resource exists, it is returned.
    """

    self.require_state('init')

    return self.__resources.add_resource(r)

  def ensure_transition(self, t):
    self.require_state('init')

    return self.__resources.add_transition(t)

  def ensure_dependency(self, r0, r1):
    return self.__resources.add_dependency(r0, r1)

  def ensure_frozen(self):
    """
    Build the finished dependency graph.

    Resolve references, merge identical realizables, collect what can be.
    """

    if self.__state == 'frozen':
      return
    self.require_state('init')
    # Order is important
    self._expand()
    self._collect()
    self._expand_aggregates()
    self.__state = 'frozen'

  def _resolve_references(self):
    self.require_state('init')
    # References were dropped for now. Reinstate them if a use case comes up.

  def _collect(self):
    # Collects compatible nodes into merged nodes.
    self.require_state('init')

    def can_merge(part0, part1):
      for n0 in part0:
        for n1 in part1:
          if self.__resources.resources_connected(n0, n1):
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
          [r for r in self.__resources.iter_resources() if collector.filter(r)])
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
          if not bool(part):
            # Test for emptiness.
            # Aggregate even singletons.
            continue
          merged = collector.collect(part)
          self.__resources.collect_resources(part, merged)

  def _expand(self):
    # Call expand_resource for all resources,
    # including those that were added by a previous call.
    while True:
      fresh = set(r
          for r in self.__resources.iter_expandable_resources())
      if bool(fresh) == False: # Test for emptiness
        return
      for r in fresh:
        self.__resources.expand_resource(r)

  def _expand_aggregates(self):
    for a in self.__resources.iter_expandable_aggregates():
      self.__resources.expand_resource(a)
    # The rule is that aggregates can only expand into transitions.
    if self.__resources.has_expandables():
      raise RuntimeError

  def realize(self):
    """
    Realize all realizables and transitions in dependency order.
    """

    self.ensure_frozen()
    for t in self.__resources.sorted_transitions():
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

