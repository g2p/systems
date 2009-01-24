
class RealizableBase(object):
  def realize(self):
    """
    This will be called with all dependencies already realized.
    """

    raise NotImplementedError('realize')

