# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from logging import getLogger

from systems.util.contracts import ContractSupportBase, precondition
from systems.util.datatypes import ImmutableDict, Named


logger = getLogger(__name__)


class AttrType(object):
  """
  An attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self,
      none_allowed=False, default_value=None,
      valid_condition=None, pytype=None, rtype=None,
      reader=None):
    """
    name: name of the attribute
    none_allowed: whether None values are allowed
    default_value: a default value
    valid_condition: a check for valid values
    pytype: a python type values must have
    reader: reads the value from current system state
    rtype: a resource type.

    If none_allowed is True, None values are allowed, they bypass validation,
    and they will be the default. default_value cannot be set in this case.
    """

    # Handling None values does make this signature complicated.

    if none_allowed and default_value is not None:
      raise ValueError("Can't set both none_allowed and default_value")
    if pytype is not None and not isinstance(pytype, (type, tuple)):
      raise TypeError
    if rtype is not None and not isinstance(rtype, str):
      raise TypeError
    self.__none_allowed = none_allowed
    self.__default_value = default_value
    self.__valid_condition = valid_condition
    self.__pytype = pytype
    self.__rtype = rtype
    self.__reader = reader
    if default_value is not None:
      self.require_valid_value(default_value)

  @property
  def default_value(self):
    """
    The default value of the attribute, or None.

    Returning None can mean different things,
    first look at has_default_value or none_allowed.
    """

    return self.__default_value

  @property
  def has_default_value(self):
    """
    Whether the attribute can be left unset.
    """

    return self.__none_allowed or (self.__default_value is not None)

  @property
  def none_allowed(self):
    """
    Whether the attribute value defaults to None.
    """

    return self.__none_allowed

  @property
  def reader(self):
    return self.__reader

  @property
  def rtype(self):
    """
    A resource type.
    """

    return self.__rtype

  def require_valid_value(self, val):
    """
    Check the value is valid, raise if it isn't.

    Checks for None (if allowed, None bypasses validation).

    Then check pytype, rtype and validation functions.
    """

    if self.__none_allowed and val is None:
      return

    if self.__pytype is not None:
      if not isinstance(val, self.__pytype):
        raise TypeError(val, self.__pytype)

    if self.__rtype is not None:
      from systems.registry import Registry
      rtype = Registry.get_singleton().resource_types.lookup(self.__rtype)
      if not isinstance(val, Resource):
        raise TypeError(val, Resource)
      if val.rtype != rtype:
        raise TypeError(val.rtype, rtype)

    if self.__valid_condition is not None:
      if not self.__valid_condition(val):
        raise ValueError(val)

  def read_value(self, id):
    """
    Read the current state.
    """

    v = self.__reader(id)
    self.require_valid_value(v)
    return v


class SimpleType(object):
  """
  A simple type, mapping names to AttrTypes.
  """

  def __init__(self, atypes):
    """
    Define a type.

    Takes name, a name for the type, and attrs, an iterable of attributes.
    """

    self.__atypes = ImmutableDict(atypes)

  def _key(self):
    return self.atypes

  def __hash__(self):
    return hash(self._key())

  def __cmp__(self, other):
    return -cmp(other, self._key())

  def prepare_valdict(self, valdict):
    """
    Validates the valdict, adding default values explicitly.
    """

    for k in valdict:
      if k not in self.atypes:
        raise KeyError(u'Invalid attribute «%s»' % k)

    for (n, a) in self.atypes.iteritems():
      if not n in valdict:
        if a.has_default_value:
          valdict[n] = a.default_value
        else:
          raise KeyError(u'Attribute «%s» is unset' % n)
      a.require_valid_value(valdict[n])
    return valdict

  def prepare_partial_valdict(self, valdict):
    """
    Validates the valdict, without requiring all values
    and without adding default values.
    """

    for k in valdict:
      if k not in self.atypes:
        raise KeyError(u'Invalid attribute «%s»' % k)
      self.atypes[k].require_valid_value(valdict[k])
    return valdict

  @property
  def atypes(self):
    return self.__atypes


class ResourceType(Named):
  def __init__(self,
      name, instance_class, id_type, state_type, global_reader=None):
    """
    Build a ResouceType.

    name is the name that can be used to look us up once we are registered.
    instance_class is the class that will be used to create Resources
    of this type. It must be a subclass of Resource.
    id_type is the dictionary of AttrType from which we will build
    our identity type.
    state_type is like id_type for our state type.
    global_reader is a function that reads the current system state,
    if passed identity attributes.
    """

    if not issubclass(instance_class, Resource):
      raise TypeError
    Named.__init__(self, name)
    self.__instance_class = instance_class
    require_disjoint(id_type, state_type)
    self.__id_type = SimpleType(id_type)
    self.__state_type = SimpleType(state_type)
    self.__global_reader = global_reader

  def __repr__(self):
    return '<RType %s>' % self.name

  @property
  def id_type(self):
    return self.__id_type

  @property
  def state_type(self):
    return self.__state_type

  @property
  def global_reader(self):
    """
    A function to read attribute values.

    Write one when it is more convenient to read all attributes at once.
    """

    # At the moment there is no efficiency gains in global reads
    # since we want values to be fresh.
    # The only gain is the convenience of being able to write just one method.
    return self.__global_reader

  def _separate_valdict(self, valdict):
    id_valdict = dict((k, v)
        for (k, v) in valdict.iteritems()
        if k in self.__id_type.atypes)
    wanted_valdict = dict((k, v)
        for (k, v) in valdict.iteritems()
        if k in self.__state_type.atypes)
    unknown_attrs = list(k
        for k in valdict
        if k not in self.__id_type.atypes
        and k not in self.__state_type.atypes)
    if bool(unknown_attrs): # Test for non-emptiness
      raise ValueError(unknown_attrs)
    return id_valdict, wanted_valdict

  def make_instance(self, valdict):
    id_valdict, wanted_valdict = self._separate_valdict(valdict)
    return self.__instance_class(self, id_valdict, wanted_valdict)


def require_disjoint(d1, d2):
  s1 = set(d1.keys())
  s2 = set(d2.keys())
  if bool(s1.intersection(s2)): # Test for non-emptiness
    raise ValueError(s1, s2)

class TransitionType(Named):
  def __init__(self, name, instance_class, instr_type, results_type):
    if not issubclass(instance_class, Transition):
      raise TypeError
    Named.__init__(self, name)
    self.__instance_class = instance_class
    require_disjoint(instr_type, results_type)
    self.__instructions_type = SimpleType(instr_type)
    self.__results_type = SimpleType(results_type)

  @property
  def instr_type(self):
    return self.__instructions_type

  @property
  def results_type(self):
    return self.__results_type

  def make_instance(self, instr_valdict):
    return self.__instance_class(self, instr_valdict)


class Attrs(ImmutableDict):
  """
  A typed set of attribute values.
  """

  def __init__(self, stype, valdict, partial=False):
    if not isinstance(stype, SimpleType):
      raise TypeError(stype, SimpleType)
    self.__stype = stype
    if partial:
      valdict = stype.prepare_partial_valdict(valdict)
    else:
      valdict = stype.prepare_valdict(valdict)
    super(Attrs, self).__init__(valdict)

  def _key(self):
    return (self.type, super(Attrs, self)._key())

  def __hash__(self):
    return hash(self._key())

  def __cmp__(self, other):
    return -cmp(other, self._key())

  def iter_nondefault_attrs(self):
    for (name, attr) in self.__stype.atypes.iteritems():
      if self[name] != attr.default_value:
        yield (name, self[name])

  def soft_check_refs(self):
    for (name, attr) in self.__stype.atypes.iteritems():
      if attr.rtype is not None:
        ref = self[name]
        ref.soft_check()

  def iter_passed_by_ref(self):
    # XXX Subclass AttrType and write RefAttrType.
    # Propose soft and hard semantics.
    for (name, attr) in self.__stype.atypes.iteritems():
      if attr.rtype is not None:
        yield name, self[name]

  @property
  def type(self):
    return self.__stype


class ReadAttrs(object):
  """
  Attributes read from system state.
  """

  def __init__(self, id_attrs, state_type, global_reader):
    self.__id_attrs = id_attrs
    self.__state_type = state_type
    self.__global_reader = global_reader

  def __getitem__(self, key):
    attr = self.__state_type.atypes[key]

    if self.__global_reader is None:
      return attr.read_value(self.__id_attrs)

    r = self.__global_reader(self.__id_attrs)
    if r == NotImplemented:
      # Try again without a global_reader
      self.__global_reader = None
      return self[key]

    val = r[key]
    attr.require_valid_value(val)
    return val


class Identifiable(object):
  @property
  def identity(self):
    raise NotImplementedError


class Expandable(Identifiable):
  """
  Something that can expand itself into more elementary components
  in a resource graph.

  Subclass Identifiable due to ResourceGraph requirements.
  """

  def expand_into(self, resource_graph):
    """
    Place transitions and resources that realize the expandable.
    """

    raise NotImplementedError


class Resource(Expandable, ContractSupportBase):
  # Make subclasses that implement the abstract stuff.
  def __init__(self, rtype, id_valdict, wanted_valdict):
    if not isinstance(rtype, ResourceType):
      raise TypeError
    self.__rtype = rtype
    self.__id_attrs = Attrs(rtype.id_type, id_valdict)
    self.__wanted_attrs = Attrs(rtype.state_type, wanted_valdict)
    self.__read_attrs = ReadAttrs(
        self.id_attrs, self.rtype.state_type, self.rtype.global_reader)
    self.__passed_by_ref = {}

  @property
  def id_attrs(self):
    return self.__id_attrs

  @property
  def wanted_attrs(self):
    return self.__wanted_attrs

  @property
  def identity(self):
    return (self.rtype.name, self.__id_attrs)

  def _key(self):
    return (self.rtype, self.__id_attrs, self.__wanted_attrs)

  def __cmp__(self, other):
    return -cmp(other, self._key())

  def __hash__(self):
    return hash(self._key())

  def __repr__(self):
    l = list()
    l.extend(', %s=%r' % e for e in self.id_attrs.iter_nondefault_attrs())
    l.extend(', %s=%r' % e for e in self.wanted_attrs.iter_nondefault_attrs())
    return 'resource(%r%s)' % (self.rtype.name, ''.join(l))

  @property
  def rtype(self):
    return self.__rtype

  def read_attrs(self):
    """
    Attribute values as they are read from system state.
    """

    # This is a method and not a property because it is not deterministic.

    return self.__read_attrs

  @property
  def passed_by_ref(self):
    return ImmutableDict(self.__passed_by_ref)

  def pass_by_ref(self, name, value):
    self.__passed_by_ref[name] = value

  def iter_passed_by_ref(self):
    for item in self.id_attrs.iter_passed_by_ref():
      yield item
    for item in self.wanted_attrs.iter_passed_by_ref():
      yield item

  def before_expand(self, resource_graph):
    logger.debug('Before expand: %s', self)

  @precondition(before_expand)
  def expand_into(self, resource_graph):
    raise NotImplementedError


class UnresolvedReferenceError(RuntimeError):
  pass


class Transition(object):
  # Subclassing to implement abstract stuff.
  def __init__(self, ttype, instr_valdict):
    if not isinstance(ttype, TransitionType):
      raise TypeError
    self.__ttype = ttype
    self.__instructions_attrs = \
        Attrs(ttype.instr_type, instr_valdict)
    self.__results_attrs = None

  @property
  def instr_attrs(self):
    return self.__instructions_attrs

  @property
  def results_attrs(self):
    if self.__results_attrs is None:
      raise RuntimeError("realize hasn't been called yet")
    return self.__results_attrs

  def realize_impl(self):
    raise NotImplementedError

  def realize(self):
    if self.__results_attrs is not None:
      raise RuntimeError('realize cannot be called more than once')
    results = self.realize_impl()
    self.__results_attrs = Attrs(self.__ttype.results_type, results)
    return self.__results_attrs

  def __repr__(self):
    l = list()
    l.extend(', %s=%r' % e for e in self.instr_attrs.iter_nondefault_attrs())
    return 'transition(%r%s)' % (self.__ttype.name, ''.join(l))


