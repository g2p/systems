# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.util.datatypes import ImmutableDict, Named


class AttrType(object):
  """
  An attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self,
      none_allowed=False, default_value=None,
      valid_condition=None, pytype=None,
      reader=None):
    """
    name: name of the attribute
    none_allowed: whether None values are allowed
    default_value: a default value
    valid_condition: a check for valid values
    pytype: a python type values must have
    reader: reads the value from current system state

    If none_allowed is True, None values are allowed, they bypass validation,
    and they will be the default. default_value cannot be set in this case.
    """

    # Handling None values does make this signature complicated.

    if none_allowed and default_value is not None:
      raise ValueError("Can't set both none_allowed and default_value")
    self.__none_allowed = none_allowed
    self.__default_value = default_value
    self.__valid_condition = valid_condition
    self.__pytype = pytype
    self.__reader = reader

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

  def is_valid_value(self, val):
    """
    Whether the value is valid.

    Checks for None (if allowed, they bypass validation).

    Then check for pytype and validation functions.
    """

    if self.__none_allowed and val is None:
      return True

    if self.__pytype is not None:
      if not isinstance(val, self.__pytype):
        return False

    if self.__valid_condition is not None:
      if not self.__valid_condition(val):
        return False

    return True

  def read_value(self, id):
    """
    Read the current state.
    """

    v = self.__reader(id)
    if not self.is_valid_value(v):
      raise ValueError(v)
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
      if not a.is_valid_value(valdict[n]):
        raise ValueError(u'Incorrect value for attribute «%s»: «%s»' %
            (n, valdict[n]))
    return valdict

  @property
  def atypes(self):
    return self.__atypes


class ResourceType(Named):
  def __init__(self, name, instance_class, id_type, state_type):
    if not issubclass(instance_class, Resource):
      raise TypeError
    Named.__init__(self, name)
    self.__instance_class = instance_class
    require_disjoint(id_type, state_type)
    self.__id_type = SimpleType(id_type)
    self.__state_type = SimpleType(state_type)

  @property
  def id_type(self):
    return self.__id_type

  @property
  def state_type(self):
    return self.__state_type

  def make_instance(self, valdict):
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
    return self.__instance_class(self, id_valdict, wanted_valdict)

  def make_ref(self, **id_valdict):
    return ResourceRef(self, id_valdict)


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


class Attrs(object):
  """
  A typed set of attribute values.
  """

  def __init__(self, stype, valdict):
    if not isinstance(stype, SimpleType):
      raise TypeError(stype, SimpleType)
    self.__stype = stype
    self.__valdict = stype.prepare_valdict(valdict)

  def _key(self):
    return (self.__stype, frozenset(self.__valdict.iteritems()))

  def __hash__(self):
    return hash(self._key())

  def __cmp__(self, other):
    return -cmp(other, self._key())

  def __getitem__(self, key):
    return self.__valdict[key]

  @property
  def type(self):
    return self.__stype


class ReadAttrs(object):
  """
  Attributes read from system state.
  """

  def __init__(self, id_attrs, state_type):
    self.__id_attrs = id_attrs
    self.__state_type = state_type

  def __getitem__(self, key):
    attr = self.__state_type.atypes[key]
    return attr.read_value(self.__id_attrs)


class Resource(object):
  # Subclassing to implement abstract stuff.
  def __init__(self, rtype, id_valdict, wanted_valdict):
    if not isinstance(rtype, ResourceType):
      raise TypeError
    self.__rtype = rtype
    self.__id_attrs = Attrs(rtype.id_type, id_valdict)
    self.__wanted_attrs = Attrs(rtype.state_type, wanted_valdict)
    # Reads one by one
    self.__read_attrs = ReadAttrs(self.id_attrs, self.__rtype.state_type)

  @property
  def id_attrs(self):
    return self.__id_attrs

  @property
  def wanted_attrs(self):
    return self.__wanted_attrs

  @property
  def identity(self):
    return (self.__rtype.name, self.__id_attrs)

  def _key(self):
    return (self.__rtype, self.__id_attrs, self.__wanted_attrs)

  def __cmp__(self, other):
    return -cmp(other, self._key())

  def __hash__(self):
    return hash(self._key())

  def _read_attrs(self):
    """
    Read attribute values.

    Override this when it is more convenient to read all attributes at once.
    """

    return NotImplemented

  def read_attrs(self):
    """
    Attribute values as they are read from system state.
    """

    # This is a method and not a property because it changes.

    r = self._read_attrs()
    if r != NotImplemented:
      return Attrs(self.__rtype.state_type, r)
    return self.__read_attrs

  def expand_into(self, resource_graph):
    """
    Place transitions and resources that realize the resource.
    """

    # Only transitions can be evaluated, so put them as deps on the graph.
    pass


class ResourceRef(object):
  # No subclassing
  def __init__(self, rtype, id_valdict):
    if not isinstance(rtype, ResourceType):
      raise TypeError
    self.__rtype = rtype
    self.__id_attrs = Attrs(rtype.id_type, id_valdict)

  @property
  def identity(self):
    return (self.__rtype.name, self.__id_attrs)


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


