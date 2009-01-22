# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from systems.transition import Transition

class PythonCode(Transition):
  """
  Usage:
  @PythonCode
  def fun():
    pass

  Mostly useless wrapper code, I hope to get rid of that.
  """

  def __call__(self, fun):
    self.__fun = fun
    return fun

  def realize(self):
    fun()

