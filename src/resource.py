
from registry import Registry
import resourcegraph

class ResourceAttr(object):
  """
  A resource attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self, name, identifying=False, naming=False,
      default_to_none=False, default_value=None):
    # A None default_value makes this signature complicated.

    if default_to_none and default_value is not None:
      raise ValueError("Can't set both default_to_none and default_value")
    self.__name = name
    self.__identifying = identifying
    self.__naming = naming
    self.__default_to_none = default_to_none
    self.__default_value = default_value

  @property
  def name(self):
    """
    Name of the attribute.
    """

    return self.__name

  @property
  def naming(self):
    """
    A naming attribute can be used to recall a defined resource.
    """

    return self.__naming

  @property
  def identifying(self):
    """
    Identifying attributes must be unique together.
    """

    return self.__identifying

  @property
  def default_value(self):
    """
    The default value of the attribute, or None.

    Returning None can mean different things.
    First check has_default_value or default_to_none .
    """

    return self.__default_value

  @property
  def has_default_value(self):
    """
    Whether the attribute can be left unset.
    """

    return self.__default_to_none or (self.__default_value is not None)

  @property
  def default_to_none(self):
    """
    Whether the attribute value defaults to None.
    """

    return self.__default_to_none

class ResourceType(object):
  """
  A type for resources.

  Specifies what attributes must be set.
  There are two kinds of attributes:
  * identity attributes, which together determine the identity of the resource.
  Two resources differing on any of the identifying attributes are distinct.
  * other attributes, which specify a state of the identified resource.
  """

  def __init__(self, name, cls, attrs):
    """
    Define a resource type.

    Takes name, a name for the type, and attrs, an iterable of attributes.
    """

    self.__name = name
    self.__cls = cls
    self.__attr_dict = {}
    self.__id_attr_dict = {}
    self.__naming_attr = None

    for attr in attrs:
      if attr.name in self.__attr_dict:
        raise ValueErrors('Cannot have two attributes with the same name')
      else:
        self.__attr_dict[attr.name] = attr
      if attr.naming:
        if self.__naming_attr:
          raise ValueError('There must be exactly one naming attribute')
        else:
          self.__naming_attr = attr
      if attr.identifying:
        self.__id_attr_dict[attr.name] = attr

  @property
  def name(self):
    return self.__name

  def newinstance(self, valdict, graph):
    return self.__cls(type=self, valdict=valdict, graph=graph)

  def prepare_valdict(self, valdict):
    """
    Validates valdict, and explicitly adds default values to it.
    """

    for a in self.__attr_dict.itervalues():
      if not a.name in valdict:
        if a.has_default_value:
          valdict[a.name] = a.default_value
        else:
          raise KeyError('Attribute %s is unset' % a.name)

  def make_identity_dict(self, valdict):
    """
    Filters valdict for identifying attributes.

    Returns a sub-dictionary of valdict (copied).
    Does not check validity of valdict.
    """

    return dict((k, valdict[k]) for k in self.__id_attr_dict.iterkeys())

class Resource(object):
  """
  Abstract base for resources.

  A resource has dependencies, which must be realized before itself.

  A resource is caracterised by a ResourceType.
  Attributes determine the way it will be realized.
  Realising a resource means reflecting it in the current state of the system.
  """

  def __init__(self, type, valdict, graph=None):
    """
    Constructor.

    graph is the container resource graph.
    """

    if graph is None:
      graph = resourcegraph.global_graph()

    self.__type = type
    self.type.prepare_valdict(valdict)
    self._set_valdict(valdict)

    self.__graph = graph
    self.__graph.add_resource(self)

  @property
  def type(self):
    """
    The resource type, a ResourceType.
    """

    return self.__type

  @property
  def attributes(self):
    """
    A dictionary of raw attribute values.
    """

    # copy, we don't want mutability
    return dict(self.__valdict)

  def identity_attributes(self):
    """
    A dictionary of raw values of identifying attributes.
    """

    return self.type.make_identity_dict(self.__valdict)

  def _set_valdict(self, valdict):
    """
    Set valdict and validate it.

    Overriders may add additional checks.
    """

    self.__valdict = valdict

  def prepare_deps(self):
    """
    Compute dependencies and add them to the resource graph.

    Called once by the resource graph.
    """

    pass

  def is_realized(self):
    """
    Check whether the resource is currently realized.

    Not sure if this is really useful, since realize will be called anyway.
    Maybe for post-mortem when realize has raised an exception.
    """

    raise NotImplementedError('is_realized')

  def realize(self):
    """
    Realize the resource.

    Called with dependencies already realized.
    Should be left unimplemented if a collector is used
    for realizing resources of this type.
    """

    raise NotImplementedError('realize')

def call_resource(typename, graph=None, **kwargs):
  t = Registry.get_singleton().restypes[typename]
  t.newinstance(graph=graph, valdict=kwargs)


# vim: set sw=2 ts=2 et :
