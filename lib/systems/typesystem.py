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

      self.__attr_dict[attr.name] = attr
      if attr.identifying:
        self.__id_attr_dict[attr.name] = attr

  @property
  def name(self):
    return self.__name

  def make_instance(self, valdict):
    return self.__cls(type=self, valdict=valdict)

  @classmethod
  def _prepare_valdict(cls, attrs, valdict):
    for k in valdict:
      if k not in attrs:
        raise KeyError(u'Invalid attribute «%s»' % k)

    for a in attrs.itervalues():
      if not a.name in valdict:
        if a.has_default_value:
          valdict[a.name] = a.default_value
        else:
          raise KeyError(u'Attribute «%s» is unset' % a.name)
      if not a.is_valid_value(valdict[a.name]):
        raise ValueError(u'Incorrect value for attribute «%s»: «%s»' %
            (a.name, valdict[a.name]))

  def prepare_valdict(self, valdict):
    """
    Validates the valdict, adding default values explicitly.
    """

    return self._prepare_valdict(self.__attr_dict, valdict)

  def prepare_id_valdict(self, valdict):
    """
    Validates the identity valdict, adding default values explicitly.
    """

    return self._prepare_valdict(self.__id_attr_dict, valdict)

  def make_identity(self, valdict):
    """
    Makes a hashable key from the values of identifying attributes in valdict.

    Does not check validity of valdict.
    """

    # We should also add the type "category",
    # which is resource or transition.
    id_vals = frozenset((k, valdict[k]) for k in self.__id_attr_dict)
    return (self.name, id_vals)

class _TypedBase(object):
  """
  Base class for a typed object.

  Don't use directly.
  """

  def __init__(self, type, valdict):
    self.__type = type
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

class _TypedWithIdentityBase(_TypedBase):
  """
  Base class for a typed, id-able object.

  Don't use directly.
  """

  @property
  def identity(self):
    """
    A hashable, immutable key.
    """

    return self.type.make_identity(self.attributes)

class InstanceBase(_TypedWithIdentityBase):
  """
  An instance, and not a reference.

  Subclass this.
  """

  def __init__(self, type, valdict):
    type.prepare_valdict(valdict)
    super(InstanceBase, self).__init__(type, valdict)

class InstanceRef(_TypedWithIdentityBase):
  """
  A reference to an instance.

  Use, do not subclass.
  """

  def __init__(self, type, valdict):
    type.prepare_id_valdict(valdict)
    super(InstanceRef, self).__init__(type, valdict)

