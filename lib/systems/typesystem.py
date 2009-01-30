# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.util.datatypes import ImmutableDict

__all__ = ('AttrType', 'Type', 'InstanceBase', 'InstanceRef', )


class AttrType(object):
  """
  An attribute.

  This is metadata for attribute values.
  RFE: attributes that are aliases
  """

  def __init__(self,
      name, identifying=False,
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

    # Allowing None does complicate this signature.

    if none_allowed and default_value is not None:
      raise ValueError("Can't set both none_allowed and default_value")
    self.__name = name
    self.__identifying = identifying
    self.__none_allowed = none_allowed
    self.__default_value = default_value
    self.__valid_condition = valid_condition
    self.__pytype = pytype
    self.__reader = reader

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

    return self.reader(id)


class Identity(object):
  def __init__(self, type, id_valdict):
    self.__type = type
    self.__id_valdict = id_valdict

  def _key(self):
    return (self.__type.name, frozenset(self.__id_valdict.iteritems()))

  def __hash__(self):
    return hash(self._key())

  def __cmp__(self, other):
    k0, k1 = self._key(), other._key()
    if k0 == k1:
      return 0
    return cmp(k0, k1)

  @property
  def attributes(self):
    """
    Read attribute values.
    """

    return ImmutableDict(self.__id_valdict)

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

  def attr_lookup(self, attrname):
    return self.__attr_dict[attrname]

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
    id_valdict = dict((k, valdict[k]) for k in self.__id_attr_dict)
    return Identity(self, id_valdict)

class _TypedBase(object):
  """
  Base class for a typed object.

  Don't use directly.
  """

  def __init__(self, type):
    self.__type = type

  @property
  def type(self):
    """
    The resource type, a Type.
    """

    return self.__type

def ReadAttributes(object):
  """
  Attributes read from system state.
  """

  def __init__(self, id):
    self.__id = id

  def __getitem__(self, key):
    attr = self.__id.type.attr_lookup(key)
    return attr.read_value(self.__id)

class _TypedWithIdentityBase(_TypedBase):
  @property
  def identity(self):
    raise NotImplementedError

  @property
  def read_attributes(self):
    """
    A read-only dictionary of attribute values,
    as they are read from system state.
    """

    return ReadAttributes(self.identity)

class InstanceBase(_TypedWithIdentityBase):
  """
  An instance, and not a reference.

  Subclass this.
  """

  def __init__(self, type, valdict):
    type.prepare_valdict(valdict)
    self.__valdict = valdict
    super(InstanceBase, self).__init__(type)

  @property
  def attributes(self):
    """
    A dictionary of raw attribute values.
    """

    i = ImmutableDict(self.__valdict)
    if i is None:
      raise TypeError
    return i

  @property
  def identity(self):
    """
    A hashable, immutable key.
    """

    return self.type.make_identity(self.__valdict)

class InstanceRef(_TypedWithIdentityBase):
  """
  A reference to an instance.

  Use, do not subclass.
  """

  def __init__(self, type, id_valdict):
    type.prepare_id_valdict(id_valdict)
    self.__id_valdict = id_valdict
    super(InstanceRef, self).__init__(type)

  @property
  def identity(self):
    """
    A hashable, immutable key.
    """

    return self.type.make_identity(self.__id_valdict)

