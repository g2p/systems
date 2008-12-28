# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from decorators import propget, propset, propdel
from registry import Registry
from context import global_context


class ResourceAttr(object):
  """
  A resource attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self, name, identifying=False, naming=False,
      default_to_none=False, default_value=None, valid_condition=None):
    # A None default_value makes this signature complicated.

    if default_to_none and default_value is not None:
      raise ValueError("Can't set both default_to_none and default_value")
    self.__name = name
    self.__identifying = identifying
    self.__naming = naming
    self.__default_to_none = default_to_none
    self.__default_value = default_value
    self.__valid_condition = valid_condition

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

    Returning None can mean different things,
    first look at has_default_value or default_to_none.
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

  def is_valid_value(self, val):
    """
    Whether the value is valid.
    """

    if self.__valid_condition is None:
      return True

    return self.__valid_condition(val)


class ResourceType(object):
  """
  A type for resources.

  Specifies what attributes must be set.
  There are two kinds of attributes:
  * identifying attributes, which together determine
  the identity of the resource.
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

  def ensure(self, valdict, context, extra_deps):
    """
    Ensure a resource is present within context.
    """

    i = self.__cls(type=self, valdict=valdict, context=context)
    return context.ensure_resource(i, extra_deps, False)

  def ensure_ref(self, valdict, context, extra_deps):
    """
    Ensure a resource reference is present within context.

    The context will later make sure the reference is valid.
    """

    ref = ResourceRef(type=self, valdict=valdict, context=context)
    return context.ensure_resource(ref, extra_deps, True)

  def prepare_valdict(self, valdict, identifying_only=False):
    """
    Validates valdict, and explicitly adds default values to it.
    """

    for k in valdict:
      if k not in self.__attr_dict:
        raise KeyError('Invalid attribute %s' % k)

    for a in self.__attr_dict.itervalues():
      if identifying_only and not a.identifying:
        continue
      if not a.name in valdict:
        if a.has_default_value:
          valdict[a.name] = a.default_value
        else:
          raise KeyError('Attribute %s is unset' % a.name)
      if not a.is_valid_value(valdict[a.name]):
        raise ValueError('Incorrect value for attribute %s: %s' %
            (a.name, valdict[a.name]))

  def make_identity_dict(self, valdict):
    """
    Filters valdict for identifying attributes.

    Returns a sub-dictionary of valdict (copied).
    Does not check validity of valdict.
    """

    return dict((k, valdict[k]) for k in self.__id_attr_dict)


class ResourceBase(object):
  """
  Abstract base for resources.
  """

  def __init__(self, type, valdict, context, identifying_only):
    self.__type = type
    self.type.prepare_valdict(valdict, identifying_only)
    self.__valdict = valdict
    self.__context = context
    self.__identifying_only = identifying_only

  @property
  def type(self):
    """
    The resource type, a ResourceType.
    """

    return self.__type

  @property
  def context(self):
    """
    The context within which unicity constraints hold
    """

    return self.__context

  @property
  def attributes(self):
    """
    A dictionary of raw attribute values.
    """

    # copy, we don't want mutability
    return dict(self.__valdict)

  @property
  def identifying_attributes(self):
    """
    A dictionary of raw values of identifying attributes.
    """

    if self.__identifying_only:
      return self.attributes
    else:
      return self.type.make_identity_dict(self.__valdict)

  @property
  def identity(self):
    """
    A static (hashable) key.
    """

    return frozenset(self.identifying_attributes.iteritems())


class Resource(ResourceBase):
  """
  A resource has dependencies, which must be realized before itself.

  A resource is caracterised by a ResourceType.
  Attributes determine the way it will be realized.
  Realising a resource means reflecting it in the current state of the system.
  """

  def __init__(self, type, valdict, context):
    super(Resource, self).__init__(
        type, valdict, context, identifying_only=False)
    self._check_valdict()

  def _check_valdict(self):
    """
    Additional checks for invalid combinations of attributes.

    Individual attributes have already been checked,
    but the combination hasn't.

    You may raise a ValueError if the values are incorrect together.
    """

    pass

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

class ResourceRef(ResourceBase):
  """
  Reference to a Resource.
  """

  def __init__(self, type, valdict, context):
    super(ResourceRef, self).__init__(
        type, valdict, context, identifying_only=True)


def ensure_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().restypes[typename]
  res = t.ensure(valdict=kwargs, context=context, extra_deps=depends)
  return res

def ref_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().restypes[typename]
  ref = t.ensure_ref(valdict=kwargs, context=context, extra_deps=depends)
  return ref


