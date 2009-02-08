# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from logging import getLogger

import networkx as NX

from systems.collector import Aggregate, CResource
from systems.registry import get_registry
from systems.typesystem import EResource, Transition, ResourceRef
from systems.util.datatypes import ImmutableDict

__all__ = ('Realizer', )


LOGGER = getLogger(__name__)


DESC_LIMIT = 64

def describe(thing):
  return '%s' % str(thing)[:DESC_LIMIT]

class CycleError(Exception):
  pass

class Node(object):
  def __init__(self):
    if type(self) == Node:
      raise TypeError

  def __repr__(self):
    return '<%s>' % self

  def __str__(self):
    return type(self).__name__

class CheckPointNode(Node):
  pass

class ExpandableNode(Node):
  def __init__(self, res):
    super(ExpandableNode, self).__init__()
    if type(self) == ExpandableNode:
      # Abstract class
      raise TypeError
    self._res = res

class BeforeExpandableNode(ExpandableNode):
  def __str__(self):
    return 'Before %s' % self._res

class AfterExpandableNode(ExpandableNode):
  def __str__(self):
    return 'After %s' % self._res

class GraphFirstNode(Node):
  pass

class GraphLastNode(Node):
  pass

node_types = (Node, Transition, Aggregate, CResource, EResource, ResourceRef)

class ResourceGraph(object):
  """
  A graph of resources and transitions linked by dependencies.

  Resources are positioned as two sentinels in the transition graph.

  Invariant: directed, acyclic.
  """

  def __init__(self, top=None):
    self._graph = NX.DiGraph()
    self._first = GraphFirstNode()
    self._last = GraphLastNode()
    self._graph.add_edge(self._first, self._last)
    # Contains CResource and EResource, despite the name.
    # Used to enforce max one resource per id.
    self.__expandables = {}
    # Received references, by name.
    self.__received_refs = {}
    # What nodes were processed (meaning expanding or collecting)
    self.__processed = set()
    # Pre-bound args pased by ref. Allow putting extra depends on them.
    self.__prebound = {}
    if top is not None:
      if not isinstance(top, ResourceGraph):
        raise TypeError(top, ResourceGraph)
      self.__top = top
    else:
      self.__top = self

  def sorted_transitions(self):
    return [n for n in NX.topological_sort(self._graph)
        if isinstance(n, Transition)]

  def iter_uncollected_resources(self):
    for nod in self._graph.nodes_iter():
      if isinstance(nod, CResource):
        if not nod in self.__processed:
          yield nod

  def iter_unexpanded_resources(self):
    for nod in self._graph.nodes_iter():
      if isinstance(nod, EResource) and not isinstance(nod, CResource):
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

    if not isinstance(resource, (CResource, EResource)):
      raise TypeError(resource, (CResource, EResource))

    if resource.identity in self.__expandables:
      # We have this id already.
      # Either it's the exact same resource, or a KeyError is thrown.
      return self._intern(resource)
    prebound = ResourceGraph(self.__top)
    for (name, ref) in resource.iter_passed_by_ref():
      # arg_refnode will be present in both graphs.
      self._pass_by_ref(prebound, name, ref)
    self.__prebound[resource.identity] = prebound
    self.__expandables[resource.identity] = resource
    return self._add_node(resource, depends)

  def make_ref(self, res, depends=()):
    res = self._intern(res)
    if not isinstance(res, (CResource, EResource)):
      raise TypeError(res, (CResource, EResource))
    depends = list(depends)
    depends.append(res)
    return self._add_node(ResourceRef(res), depends)

  def add_to_top(self, res):
    """
    Add a resource to the top ResourceGraph.

    Use it to put things that you don't necessarily
    want to be after the outside dependencies the current graph has.
    """

    res = self.__top.add_resource(res)
    ref = self.__top.make_ref(res)
    return self._add_node(ref)

  def _refs_received(self):
    return ImmutableDict(self.__received_refs)

  def _refs_passed(self, item):
    item = self._intern(item)
    return self.__prebound[item.identity]._refs_received()

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
      raise KeyError(thing)
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
    # XXX pygraphviz has steep dependencies (x11 libs)
    # and recommends (texlive) for a headless box.

    # We duplicate the graph, otherwise networkx / pygraphviz
    # would make a lossy conversion (sometimes refusing to convert), by adding
    # nodes as their string representation. Madness, I know.
    gr2 = NX.create_empty_copy(self._graph, False)
    for node in self._graph.nodes_iter():
      gr2.add_node(id(node))
    for (n0, n1) in self._graph.edges_iter():
      gr2.add_edge(id(n0), id(n1))
    names = dict((id(node), { 'label': describe(node)})
        for node in self._graph.nodes_iter())
    gr2.delete_node(id(self._first))
    gr2.delete_node(id(self._last))
    g = NX.to_agraph(gr2, {
        'graph': {
          'nodesep': '0.2',
          'rankdir': 'TB',
          'ranksep': '0.5',
          },
        'node': {
          'shape': 'box',
          },
        },
        names)
    g.write(fname + '.dot')
    # Dot is good for DAGs.
    g.layout(prog='dot')
    g.draw(fname + '.svg')
    NX.write_yaml(self._graph, fname + '.yaml')

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

    for r0 in r0s:
      r0 = self._intern(r0)
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
    n0 = self._intern(n0)
    n1 = self._intern(n1)
    self.require_acyclic()
    # list is used as a temporary
    # add after delete in case of same.
    for pred in list(self._graph.predecessors_iter(n0)):
      self._graph.delete_edge(pred, n0)
      self._graph.add_edge(pred, n1)
    for succ in list(self._graph.successors_iter(n0)):
      self._graph.delete_edge(n0, succ)
      self._graph.add_edge(n1, succ)
    self._graph.delete_node(n0)
    # Can't undo. Invariant will stay broken.
    self.require_acyclic()

  def _split_node(self, res):
    res = self._intern(res)
    before = self._add_node(BeforeExpandableNode(res))
    after = self._add_node(AfterExpandableNode(res))
    self._graph.add_edge(before, after)
    for pred in list(self._graph.predecessors_iter(res)):
      self._graph.delete_edge(pred, res)
      self._graph.add_edge(pred, before)
    for succ in list(self._graph.successors_iter(res)):
      self._graph.delete_edge(res, succ)
      self._graph.add_edge(after, succ)
    self._graph.delete_node(res)
    return before, after

  def _receive_by_ref(self, name, ref):
    if name in self.__received_refs:
      raise RuntimeError(name, ref)
    ref = self._add_node(ref)
    self.__received_refs[name] = ref
    return ref

  def _pass_by_ref(self, subgraph, name, ref):
    # The origin/value distinction is important
    # for aliased arguments (two refs, same val).
    ref = self._intern(ref)
    if not isinstance(ref, ResourceRef):
      raise TypeError(ref, ResourceRef)

    subgraph._receive_by_ref(name, ref)

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

    if isinstance(res, EResource):
      resource_graph = self.__prebound[res.identity]
    elif isinstance(res, Aggregate):
      resource_graph = ResourceGraph(self.__top)
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
      # We expand from the outside in.
      assert res1 not in self.__processed
      if id1 in self.__expandables:
        # Pass by reference if you must use the same resource
        # in different contexts.
        raise RuntimeError('ResourceBase collision.', res, res1)
      else:
        self.__expandables[id1] = res1

    before, after = self._split_node(res)
    self.__processed.add(res)
    self._move_edges(resource_graph._first, before)
    self._move_edges(resource_graph._last, after)
    # What may break the invariant:
    # A dependency is put before a resource (through another dependency),
    # but the resource also calls up the same dependency internally.
    # The problem is, the dependency appears at both sides
    # of resource._before.
    self.require_acyclic()


class Realizer(object):
  """
  A graph of realizables linked by dependencies.
  """

  def __init__(self, expandable):
    self.__resources = ResourceGraph()
    self.__expandable = expandable
    self.__state = 'init'

  def require_state(self, state):
    """
    Raise an exception if we are not in the required state.
    """

    if self.__state != state:
      raise RuntimeError(u'Realizer state should be «%s»' % state)

  def ensure_frozen(self):
    """
    Build the finished dependency graph.

    Merge identical realizables, collect what can be.
    """

    if self.__state == 'frozen':
      return
    # Order is important
    self.require_state('init')
    self.__expandable.expand_into(self.__resources)
    self.__resources.draw('/tmp/freezing')
    self._expand()
    self.__resources.draw('/tmp/pre-collect')
    self._collect()
    self._expand_aggregates()
    assert not bool(list(self.__resources.iter_unprocessed()))
    self.__state = 'frozen'
    self.__resources.draw('/tmp/frozen')

  def _collect(self):
    # Collects compatible nodes into merged nodes.

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

    reg = get_registry()
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
    for t in self.__resources.sorted_transitions():
      t.realize()
    self.__state = 'realized'


