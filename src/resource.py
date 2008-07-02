
import resourcegraph

class ResourceAttr(object):
  """
  A resource attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self, name, identifying=False, naming=False):
    self.__name = name
    self.__identifying = identifying
    self.__naming = naming

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

class ResourceType(object):
  """
  A type for resources.

  Specifies what attributes must be set.
  There are two kinds of attributes:
  * identity attributes, which together determine the identity of the resource.
  Two resources differing on any of the identifying attributes are distinct.
  * other attributes, which specify a state of the identified resource.
  """

  def __init__(self, name, attrs):
    """
    Define a resource type.

    Takes name, a name for the type, and attrs, an iterable of attributes.
    """

    self.__type_name = name
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

  def validate(self, valdict):
    """
    Check that a dictionary of name, value match the type.

    Raise an exception otherwise.
    """

    pass

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

    self.__graph = graph
    self.__graph.add_resource(self)
    self.__type = type
    self.__valdict = valdict

    type.validate(valdict)

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

# vim: set sw=2 ts=2 et :
