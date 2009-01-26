class Collector(object):
  def __init__(self, name):
    self.__name = name

  @property
  def name(self):
    return self.__name

  def collect(self, context):
    raise NotImplementedError('collect')

