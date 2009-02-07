# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from logging import getLogger
import traceback

import networkx as NX

from systems.collector import Aggregate, CollectibleResource
from systems.registry import Registry
from systems.typesystem import Resource, Transition

__all__ = ('Context', 'global_context', )


logger = getLogger(__name__)


REPR_LIMIT = 32

class CycleError(Exception):
  pass

class Node(object):
  def __repr__(self):
    return '<%s @ %s>' % (type(self).__name__, hash(self))

class CheckPointNode(Node):
  pass

class ExpandableNode(Node):
  def __init__(self, res):
    if type(self) == ExpandableNode:
      # Abstract class
      raise TypeError
    self._res = res

class BeforeExpandableNode(ExpandableNode):
  def __repr__(self):
    return '<Before %s @ %s>' % (repr(self._res)[:REPR_LIMIT], hash(self))

class AfterExpandableNode(ExpandableNode):
  def __repr__(self):
    return '<After %s @ %s>' % (repr(self._res)[:REPR_LIMIT], hash(self))

class GraphFirstNode(Node):
  pass

class GraphLastNode(Node):
  pass

class ExpandableByRefNode(Node):
  def __init__(self, res):
    self._res = res

def describe(thing):
    return '<%s @ %s>' % (repr(thing)[:REPR_LIMIT], hash(thing))

node_types = (Node, Transition, Aggregate, CollectibleResource, Resource)

class ResourceGraph(object):
  """
  A graph of resources and transitions linked by dependencies.

  Resources are positioned as two sentinels in the transition graph.

  Invariant: directed, acyclic.
  """

  def __init__(self):
    self._graph = NX.DiGraph()
    self._first = GraphFirstNode()
    self._last = GraphLastNode()
    self._graph.add_edge(self._first, self._last)
    # XXX CollectibleResource shouldn't really be expandable.
    self.__expandables = {}
    # A multimap of references.
    self.__corefs = {}
    # What nodes were processed (meaning expanding or collecting)
    self.__processed = set()
    # Pre-bound args pased by ref. Allow putting extra depends on them.
    self.__prebound = {}

  def sorted_transitions(self):
    return [n for n in NX.topological_sort(self._graph)
        if isinstance(n, Transition)]

  def iter_uncollected_resources(self):
    for nod in self._graph.nodes_iter():
      if isinstance(nod, CollectibleResource):
        if not nod in self.__processed:
          yield nod

  def iter_unexpanded_resources(self):
    for nod in self._graph.nodes_iter():
      if isinstance(nod, Resource) and not isinstance(nod, CollectibleResource):
        if not nod in self.__processed:
          yield nod

  def iter_unexpanded_aggregates(self):
    for agg in self._graph.nodes_iter():
      if isinstance(agg, Aggregate):
        if not agg in self.__processed:
          yield agg

  def iter_unprocessed(self):
    for nod in self.iter_uncollected_resources():
      yield nod
    for nod in self.iter_unexpanded_resources():
      yield nod
    for nod in self.iter_unexpanded_aggregates():
      yield nod

  def has_unprocessed(self):
    l = list(self.iter_unprocessed())
    return bool(l) # Tests for non-emptiness

  def require_acyclic(self):
    if not NX.is_directed_acyclic_graph(self._graph):
      # XXX NX doesn't have a 1-line method for listing those cycles
      raise CycleError

  def _add_node(self, node, depends=()):
    if not isinstance(node, node_types):
      raise TypeError(node, node_types)
    self._graph.add_node(node)
    self._graph.add_edge(self._first, node)
    self._graph.add_edge(node, self._last)
    for dep in depends:
      depn = self._intern(dep)
      self._add_node_dep(depn, node)
    return node

  def add_checkpoint(self, depends=()):
    return self._add_node(CheckPointNode(), depends)

  def add_transition(self, transition, depends=()):
    if not isinstance(transition, Transition):
      raise TypeError(transition, Transition)
    return self._add_node(transition, depends)

  def _add_aggregate(self, aggregate, depends=()):
    if not isinstance(aggregate, Aggregate):
      raise TypeError(aggregate, Aggregate)
    return self._add_node(aggregate, depends)

  def add_resource(self, resource, depends=()):
    """
    Add a resource.

    If an identical resource exists, it is returned.
    """

    if not isinstance(resource, (CollectibleResource, Resource)):
      raise TypeError(resource, (CollectibleResource, Resource))

    if resource.identity in self.__expandables:
      r2 = self._intern(resource)
      if resource == r2:
        return r2
      # Avoid confusion with processed stuff or different depends.
      raise RuntimeError(resource, r2)
    prebound = ResourceGraph()
    for (name, arg) in resource.iter_passed_by_ref():
      # arg_refnode will be present in both graphs.
      arg_refnode = self.make_reference(arg)
      prebound._add_node(arg_refnode)
      resource.pass_by_ref(name, arg_refnode)
    self.__prebound[resource.identity] = prebound
    self.__expandables[resource.identity] = resource
    return self._add_node(resource, depends)

  def _add_node_dep(self, node0, node1):
    if not isinstance(node0, node_types):
      raise TypeError(node0, node_types)
    if not isinstance(node1, node_types):
      raise TypeError(node1, node_types)
    if not self._graph.has_node(node0):
      raise KeyError(node0)
    if not self._graph.has_node(node1):
      raise KeyError(node1)
    if self._graph.has_edge(node0, node1):
      return False
    if node0 == node1:
      # Disallow self-loops to keep acyclic invariant.
      # Also they don't make sense.
      raise ValueError(node0)
    rev_path = NX.shortest_path(self._graph, node1, node0)
    if rev_path is not False:
      raise CycleError(rev_path)
    self._graph.add_edge(node0, node1)
    return True

  def _intern(self, thing):
    if not isinstance(thing, node_types):
      raise TypeError
    if thing not in self._graph:
      raise KeyError(node)
    if isinstance(thing, (CollectibleResource, Resource)):
      assert thing == self.__expandables[thing.identity]
    return thing

  def add_dependency(self, elem0, elem1):
    node0 = self._intern(elem0)
    node1 = self._intern(elem1)
    return self._add_node_dep(node0, node1)

  def _is_direct_rconnect(self, r0, r1):
    s0 = self._intern(r0)
    s1 = self._intern(r1)
    # shortest_path is also a test for connectedness.
    return bool(NX.shortest_path(self._graph, s0, s1))

  def resources_connected(self, r0, r1):
    return self._is_direct_rconnect(r0, r1) \
        or self._is_direct_rconnect(r1, r0)

  def draw(self, fname):
    return self.draw_agraph(fname)

  def draw_agraph(self, fname):
    g = NX.to_agraph(self._graph, {
        'graph': {
          'nodesep': '0.2',
          'rankdir': 'TB',
          'ranksep': '0.5',
          },
        'node': {
          'shape': 'box',
          },
        })
    g.layout(prog='dot')
    g.draw(fname)

  def draw_matplotlib(self, fname):
    # Pyplot is stateful and awkward to use.
    import matplotlib.pyplot as P
    # Disable hold or it definitely won't work (probably a bug).
    P.hold(False)
    NX.draw(self._graph)
    P.savefig(fname)

  def collect_resources(self, r0s, r1):
    """
    Replace an iterable of resources with one new resource.

    May break the acyclic invariant, caveat emptor.
    """

    # The invariant is kept iff the r0s don't have paths linking them.
    # For our use case (collectors), we could allow paths provided they are
    # internal to r0s. This introduces self-loops that we would then remove.

    if r1.identity in self.__expandables:
      raise ValueError
    for r0 in r0s:
      r0 = self._intern(r0)
      if r0.identity == r1.identity:
        raise ValueError(r0)
      if r0 in self.__processed:
        raise RuntimeError

    r1 = self._add_aggregate(r1)
    r1 = self._intern(r1)

    for r0 in r0s:
      r0 = self._intern(r0)
      self._move_edges(r0, r1)
      self.__processed.add(r0)

  def _move_edges(self, n0, n1):
    if n0 == n1:
      raise RuntimeError
    if n0 not in self._graph:
      raise KeyError
    if n1 not in self._graph:
      raise KeyError
    self.require_acyclic()
    # list is used as a temporary
    # add after delete in case of same.
    for pred in list(self._graph.predecessors_iter(n0)):
      self._graph.delete_edge(pred, n0)
      self._graph.add_edge(pred, n1)
    for succ in list(self._graph.successors_iter(n0)):
      self._graph.delete_edge(n0, succ)
      self._graph.add_edge(n1, succ)
    # Can't undo. Invariant will stay broken.
    self.require_acyclic()

  def _split_node(self, res):
    before = self._add_node(BeforeExpandableNode(res))
    after = self._add_node(AfterExpandableNode(res))
    self._graph.add_edge(before, after)
    for pred in list(self._graph.predecessors_iter(res)):
      self._graph.delete_edge(pred, res)
      self._graph.add_edge(pred, before)
    for succ in list(self._graph.successors_iter(res)):
      self._graph.delete_edge(res, succ)
      self._graph.add_edge(after, succ)
    return before, after

  def make_reference(self, res, depends=()):
    if res.identity not in self.__expandables \
        and res.identity not in self.__corefs:
      pass
      # XXX Can't remember why
      #raise RuntimeError(res)
    corefs = self.__corefs.setdefault(res.identity, list())
    ref = self._add_node(ExpandableByRefNode(res), depends)
    corefs.append(ref)
    return ref

  def expand_resource(self, res):
    """
    Replace res by a small resource graph.

    The resource_graph is inserted in the main graph
    between the sentinels that represent the resource.
    """

    res = self._intern(res)

    # We're processing from the outside in.
    if res in self.__processed:
      raise RuntimeError

    if isinstance(res, Resource):
      resource_graph = self.__prebound[res.identity]
    elif isinstance(res, Aggregate):
      resource_graph = ResourceGraph()
    else:
      raise TypeError
    res.expand_into(resource_graph)
    if bool(resource_graph.__processed):
      raise RuntimeError

    # Do not skip sentinels.
    for n in resource_graph._graph.nodes_iter():
      self._add_node(n)
    for (n0, n1) in resource_graph._graph.edges_iter():
      self._add_node_dep(n0, n1)

    for (id1, rg1) in resource_graph.__prebound.iteritems():
      if id1 in self.__prebound:
        raise RuntimeError
      self.__prebound[id1] = rg1

    for (id1, res1) in resource_graph.__expandables.iteritems():
      assert res1 not in self.__processed
      if id1 in self.__expandables:
        # Pass by reference if you must use the same resource
        # in different contexts.
        raise RuntimeError('Resource collision.', res, res1)
      else:
        self.__expandables[id1] = res1

    before, after = self._split_node(res)
    self._move_edges(resource_graph._first, before)
    self._move_edges(resource_graph._last, after)
    # Never delete; we must still be able to identify
    # to avoid redundant expansion.
    self.__processed.add(res)
    # XXX Problematic:
    # A dependency is put before a resource (through another dependency),
    # but the resource also calls up the same dependency internally.
    # The problem is, the dependency appears at both sides
    # of resource._before.
    self.require_acyclic()


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

    Merge identical realizables, collect what can be.
    """

    if self.__state == 'frozen':
      return
    self.require_state('init')
    # Order is important
    self._expand()
    self._collect()
    self._expand_aggregates()
    assert not bool(list(self.__resources.iter_unprocessed()))
    self.__state = 'frozen'

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
          [r for r in self.__resources.iter_uncollected_resources()
            if collector.filter(r)])
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
    assert not bool(list(self.__resources.iter_uncollected_resources()))

  def _expand(self):
    # Poor man's recursion
    while True:
      fresh = set(r
          for r in self.__resources.iter_unexpanded_resources())
      if bool(fresh) == False: # Test for emptiness
        break
      for r in fresh:
        self.__resources.expand_resource(r)
    assert not bool(list(self.__resources.iter_unexpanded_resources()))

  def _expand_aggregates(self):
    for a in list(self.__resources.iter_unexpanded_aggregates()):
      self.__resources.expand_resource(a)
    assert not bool(list(self.__resources.iter_unexpanded_aggregates()))
    # Enforce the rule that aggregates can only expand into transitions.
    if self.__resources.has_unprocessed():
      raise RuntimeError(list(self.__resources.iter_unprocessed()))

  def realize(self):
    """
    Realize all realizables and transitions in dependency order.
    """

    self.ensure_frozen()
    self.__resources.draw('frozen.svg') # XXX
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

