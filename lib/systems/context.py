# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from logging import getLogger
import traceback

import networkx as NX

from systems.collector import Aggregate, CollectibleResource
from systems.registry import Registry
from systems.typesystem import Resource, Transition, ResourceRef, Expandable

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

class ResourceRefNode(Node):
  def __init__(self, ref):
    self.__ref = ref

  @property
  def reference(self):
    return self.__ref

  def __repr__(self):
    return '<Ref to a %s @ %s>' % (self.__ref.rtype, hash(self))

class TransitionNode(Node):
  def __init__(self, transition):
    self.__transition = transition

  @property
  def transition(self):
    return self.__transition

  def __repr__(self):
    return '<Transition %s @ %s>' % (repr(self.transition)[:REPR_LIMIT], hash(self))


class ExpandableInGraph(object):
  """
  An expandable can't be put directly in a graph;
  it must be represented by two nodes (before and after).
  """

  def __init__(self, graph, res, before, after):
    if not isinstance(res, Expandable):
      raise TypeError(res, Expandable)
    self._res = res
    self._before = before
    self._after = after
    # Processing is either expanding or collecting.
    self._processed = False

    self._resource_graph = ResourceGraph()
    if isinstance(res, Aggregate):
      return
    for (name, arg) in res.iter_passed_by_ref():
      # arg_refnode will be present in both graphs.
      arg_refnode = graph.make_reference(arg)
      self._resource_graph._add_node(arg_refnode)
      res.pass_by_ref(name, arg_refnode)

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
    # Stores ExpandableInGraph entries.
    # XXX CollectibleResource shouldn't really be expandable.
    self.__expandables = {}
    # Stores ref lists by ids. Those references are deprecated.
    self.__refs = {}
    # A totally different kind of reference.
    self.__corefs = {}
    # Map transitions to nodes
    self.__tr_nodes = {}
    # Map refs to nodes
    self.__ref_nodes = {}

  def sorted_transitions(self):
    return [n.transition for n in NX.topological_sort(self._graph)
        if isinstance(n, TransitionNode)]

  def iter_sorted_unexpanded_resources(self):
    for n in NX.topological_sort(self._graph):
      if isinstance(n, BeforeExpandableNode):
        res = n._res
        if not isinstance(res, Resource) \
            or isinstance(res, CollectibleResource):
              continue
        eig = self.__expandables[res.identity]
        if eig._processed:
          continue
        yield res

  def iter_references(self):
    for coref_list in self.__refs.itervalues():
      for ref in coref_list:
        yield ref

  def iter_unresolved_references(self):
    for ref in self.iter_references():
      if not ref.bound:
        yield ref

  def has_unresolved_references(self):
    l = list(self.iter_unresolved_references())
    return bool(l) # Tests for non-emptiness

  def iter_unprocessed(self):
    for eig in self.__expandables.itervalues():
      if not eig._processed:
        yield eig._res

  def iter_uncollected_resources(self):
    for res in self.iter_unprocessed():
      if isinstance(res, CollectibleResource):
        yield res

  def iter_unexpanded(self):
    for res in self.iter_unprocessed():
      # CollectibleResource isn't really an Expandable despite inheritance
      if not isinstance(res, CollectibleResource):
        yield res

  def iter_unexpanded_resources(self):
    for res in self.iter_unexpanded():
      if isinstance(res, Resource):
        yield res

  def iter_unexpanded_aggregates(self):
    for res in self.iter_unexpanded():
      if isinstance(res, Aggregate):
        yield res

  def has_unexpanded(self):
    l = list(self.iter_unexpanded())
    return bool(l) # Tests for non-emptiness

  def resource_at(self, key):
    r = self.__expandables[key]._res
    if not isinstance(r, Resource):
      raise TypeError(r, Resource)
    return r

  def require_acyclic(self):
    if not NX.is_directed_acyclic_graph(self._graph):
      # XXX NX doesn't have a 1-line method for listing those cycles
      raise CycleError

  def _add_node(self, node, depends=()):
    if not isinstance(node, Node):
      raise TypeError(node, Node)
    self._graph.add_node(node)
    self._graph.add_edge(self._first, node)
    self._graph.add_edge(node, self._last)
    r = node
    for dep in depends:
      self.add_dependency(dep, node)
    return r

  def add_checkpoint(self, depends=()):
    return self._add_node(CheckPointNode(), depends)

  def add_transition(self, transition, depends=()):
    if not isinstance(transition, Transition):
      raise TypeError(transition, Transition)
    node = TransitionNode(transition)
    node = self._add_node(node, depends)
    self.__tr_nodes[transition] = node
    return node.transition

  def add_resource(self, resource, depends=()):
    """
    Add a resource.

    If an identical resource exists, it is returned.
    """

    if not isinstance(resource, Resource):
      raise TypeError(resource, Resource)
    res = self._add_expandable(resource, depends)
    self._may_resolve_refs(res.identity)
    if res.rtype.name == 'PgUserXX':
      logger.debug(traceback.format_stack())
    return res

  def add_reference(self, ref, depends=()):
    """
    Add a reference.

    ref is a constrained reference, and the context uses soft-reference
    semantics. This means that the reference either exists, or a resource
    is created read-only to see if the read state matches the constraints.
    """

    if not isinstance(ref, ResourceRef):
      raise TypeError(ref, ResourceRef)
    node = ResourceRefNode(ref)
    node = self._add_node(node, depends)
    self.__ref_nodes[ref] = node
    corefs = self.__refs.setdefault(ref.target_identity, list())
    corefs.append(ref)
    self._may_resolve_refs(ref.target_identity)
    return node.reference

  def _may_resolve_refs(self, id):
    if id not in self.__expandables or id not in self.__refs:
      return False
    res = self.resource_at(id)
    corefs = self.__refs[id]
    for ref in corefs:
      if ref.bound:
        continue
      logger.debug('Resolving: %s', ref)
      self.add_dependency(res, ref)
      ref.bind_to(res)
    return True

  def _add_expandable(self, expandable, depends=()):
    if not isinstance(expandable, Expandable):
      raise TypeError(expandable, (Resource, Aggregate))

    if expandable.identity in self.__expandables:
      eig = self.__expandables[expandable.identity]
      r2 = eig._res
      if expandable == r2:
        return r2
      # Avoid confusion with processed stuff or different depends.
      raise RuntimeError(expandable, r2)
    before = BeforeExpandableNode(expandable)
    after = AfterExpandableNode(expandable)
    self._add_node(before, depends)
    self._add_node(after)
    self._add_node_dep(before, after)
    self.__expandables[expandable.identity] = \
        ExpandableInGraph(self, expandable, before, after)
    return expandable

  def _add_node_dep(self, node0, node1):
    if not isinstance(node0, Node):
      raise TypeError(node0, Node)
    if not isinstance(node1, Node):
      raise TypeError(node1, Node)
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
    rev_path = NX.shortest_path(self._graph, node1, node0)
    if rev_path is not False:
      raise CycleError(rev_path)
    self._graph.add_edge(node0, node1)
    return True

  def _nodeify(self, thing):
    if isinstance(thing, Node):
      return thing
    elif isinstance(thing, Transition):
      return self.__tr_nodes[thing]
    elif isinstance(thing, ResourceRef):
      return self.__ref_nodes[thing]
    else:
      raise TypeError

  def add_dependency(self, elem0, elem1):
    if isinstance(elem0, Expandable):
      node0 = self.__expandables[elem0.identity]._after
    else:
      node0 = self._nodeify(elem0)
    if isinstance(elem1, Expandable):
      node1 = self.__expandables[elem1.identity]._before
    else:
      node1 = self._nodeify(elem1)
    return self._add_node_dep(node0, node1)

  def _is_direct_rconnect(self, r0, r1):
    s0 = self.__expandables[r0.identity]._after
    s1 = self.__expandables[r1.identity]._before
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
      if not r0.identity in self.__expandables:
        raise KeyError(r0)
      if r0.identity == r1.identity:
        raise ValueError(r0)
      eig0 = self.__expandables[r0.identity]
      if eig0._processed:
        raise RuntimeError

    r1 = self._add_expandable(r1)
    eig1 = self.__expandables[r1.identity]

    for r0 in r0s:
      eig0 = self.__expandables[r0.identity]
      self._move_edges(eig0._before, eig1._before)
      self._move_edges(eig0._after, eig1._after)
      eig0._processed = True

  def _move_edges(self, n0, n1):
    if n0 == n1:
      raise RuntimeError
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

  def make_reference(self, res, depends=()):
    if res.identity not in self.__expandables \
        and res.identity not in self.__corefs:
      pass
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

    if not res.identity in self.__expandables:
      raise KeyError(res)
    eig0 = self.__expandables[res.identity]

    if eig0._processed:
      raise RuntimeError

    resource_graph = eig0._resource_graph
    res.expand_into(resource_graph)

    # Do not skip sentinels.
    for n in resource_graph._graph.nodes_iter():
      self._add_node(n)
    for (n0, n1) in resource_graph._graph.edges_iter():
      self.add_dependency(n0, n1)

    for (id1, eig1) in resource_graph.__expandables.iteritems():
      assert not eig1._processed
      if id1 in self.__expandables:
        # Pass by reference if you must use the same resource
        # in different contexts.
        raise RuntimeError('Resource collision.', res, eig1._res)
      else:
        self.__expandables[id1] = eig1

    # XXX Problematic:
    # A dependency is put before a resource (through another dependency),
    # but the resource also calls up the same dependency internally.
    # The problem is, the dependency appears at both sides
    # of resource._before.
    self._move_edges(resource_graph._first, eig0._before)
    self._move_edges(resource_graph._last, eig0._after)
    # Never delete; we must still be able to identify
    # to avoid redundant expansion.
    eig0._processed = True
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

    Resolve references, merge identical realizables, collect what can be.
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
        if self.__resources.has_unresolved_references():
          raise RuntimeError
        self.__resources.expand_resource(r)
    if self.__resources.has_unresolved_references():
      raise RuntimeError
    assert not bool(list(self.__resources.iter_unexpanded_resources()))
    assert not bool(list(self.__resources.iter_sorted_unexpanded_resources()))

  def _expand_aggregates(self):
    for a in self.__resources.iter_unexpanded_aggregates():
      self.__resources.expand_resource(a)
    assert not bool(list(self.__resources.iter_unexpanded_aggregates()))
    # Enforce the rule that aggregates can only expand into transitions.
    if self.__resources.has_unexpanded():
      raise RuntimeError(list(self.__resources.iter_unexpanded()))

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

