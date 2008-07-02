class Registry(object):
  """
  A registry for resource types.
  """

  def __new__(cls):
    if hasattr(cls, '_singleton'):
      raise RuntimeError('Singleton has already been instanciated')
    return super(type(cls), cls).__new__(cls)

  def __init__(self):
    self.__restypes = {}

  @classmethod
  def get_singleton(cls):
    """
    Get the singleton instance.
    """

    if not hasattr(cls, '_singleton'):
      setattr(cls, '_singleton', cls())
    return getattr(cls, '_singleton')

  def register_resource_type(self, t):
    """
    Register a ResourceType
    """

    self.__restypes[t.name] = t

  @property
  def restypes(self):
    return dict(self.__restypes)

# vim: set sw=2 ts=2 et :
