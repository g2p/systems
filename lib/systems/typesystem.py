# vim: set fileencoding=utf-8 sw=2 ts=2 et :

__all__ = ('AttrType', 'Type', 'InstanceBase', 'InstanceRef', )


class AttrType(object):
  """
  An attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self, name, identifying=False,
      default_to_none=False, default_value=None, valid_condition=None):
    # A None default_value makes this signature complicated.

    if default_to_none and default_value is not None:
      raise ValueError("Can't set both default_to_none and default_value")
    self.__name = name
    self.__identifying = identifying
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
  def identifying(self):
    """
    Identifying attributes can be used to recall a defined resource.
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


class Type(object):
  """
  A type.

  Specifies what attributes must be set.
  There are two kinds of attributes:
  * identifying attributes, which together determine
  the identity of the instance.
  Two resources differing on any of the identifying attributes are distinct.
  * other attributes, which specify a state of the identified resource.
  """

  def __init__(self, name, cls, attrs):
    """
    Define a type.

    Takes name, a name for the type, and attrs, an iterable of attributes.
    """

    self.__name = name
    self.__cls = cls
    self.__attr_dict = {}
    self.__id_attr_dict = {}

    for attr in attrs:
      if attr.name in self.__attr_dict:
        raise ValueErrors('Cannot have two attributes with the same name')
      else:
        self.__attr_dict[attr.name] = attr
      if attr.identifying:
        self.__id_attr_dict[attr.name] = attr

  @property
  def name(self):
    return self.__name

  def ensure(self, valdict, context, extra_deps):
    """
    Ensure an instance is present within context.
    """

    i = self.__cls(type=self, valdict=valdict)
    return context.ensure_realizable(i, extra_deps)

  def ensure_ref(self, valdict, context, extra_deps):
    """
    Ensure a reference is present within context.

    The context will later make sure the reference is valid.
    """

    ref = InstanceRef(type=self, valdict=valdict)
    return context.ensure_realizable(ref, extra_deps)

  def prepare_valdict(self, valdict, identifying_only=False):
    """
    Validates valdict, and explicitly adds default values to it.
    """

    for k in valdict:
      if k not in self.__attr_dict:
        raise KeyError(u'Invalid attribute «%s»' % k)

    for a in self.__attr_dict.itervalues():
      if identifying_only and not a.identifying:
        continue
      if not a.name in valdict:
        if a.has_default_value:
          valdict[a.name] = a.default_value
        else:
          raise KeyError(u'Attribute «%s» is unset' % a.name)
      if not a.is_valid_value(valdict[a.name]):
        raise ValueError(u'Incorrect value for attribute «%s»: «%s»' %
            (a.name, valdict[a.name]))

  def make_identity(self, valdict):
    """
    Makes a hashable key from the values of identifying attributes in valdict.

    Does not check validity of valdict.
    """

    # We should also add the type "category",
    # which is resource or transition.
    id_vals = frozenset((k, valdict[k]) for k in self.__id_attr_dict)
    return (self.name, id_vals)

class TypedBase(object):
  """
  Base class for a typed object.
  """

  def __init__(self, type, valdict, identifying_only):
    self.__type = type
    self.type.prepare_valdict(valdict, identifying_only)
    self.__valdict = valdict

  @property
  def type(self):
    """
    The resource type, a Type.
    """

    return self.__type

  @property
  def attributes(self):
    """
    A dictionary of raw attribute values.
    """

    # copy, we don't want mutability
    return dict(self.__valdict)

  @property
  def identity(self):
    """
    A hashable, immutable key.
    """

    return self.type.make_identity(self.__valdict)

class InstanceBase(TypedBase):
  """
  An instance, not a reference
  """

  def __init__(self, type, valdict):
    super(InstanceBase, self).__init__(
        type, valdict, identifying_only=False)

class InstanceRef(TypedBase):
  """
  Reference to another instance.
  """

  def __init__(self, type, valdict):
    super(InstanceRef, self).__init__(
        type, valdict, identifying_only=True)

