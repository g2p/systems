# vim: set fileencoding=utf-8 sw=2 ts=2 et :
import re
import os
import subprocess

from systems.registry import Registry
from systems.resource import Resource, ResourceType, ResourceAttr

__all__ = ('register', )

class AptitudePackage(Resource):
  """
  A debian package, managed by aptitude

  Dependencies are not managed here.
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('AptitudePackage', cls,
      [
      ResourceAttr('name',
        identifying=True, naming=True,
        valid_condition=cls.is_valid_pkgname),
      ResourceAttr('version',
        identifying=False, naming=False, default_to_none=True,
        valid_condition=cls.is_valid_version),
      ResourceAttr('state',
        identifying=False, naming=False, default_value='installed',
        valid_condition=cls.is_valid_state),
    ])
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_pkgname(cls, name):
    # Specified here:
    # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Package
    return bool(re.match('^[a-z][a-z0-9+\.-]*[a-z0-9]$', name))

  @classmethod
  def is_valid_version(cls, version):
    if version is None:
      return True
    # From lintian's _valid_version
    # XXX can pass dashes
    # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
    return bool(
        re.match('^(\d+:)?([-\.+:~a-z0-9]+?)(-[\.+~a-z0-9]+)?$', version))

  @classmethod
  def is_valid_state(cls, state):
    # Semantics for held are unclear. Disable hold support.
    # A package can be held installed or held removed.
    # Installing and holding can't be done in a single aptitude call.
    return state in ('installed', 'uninstalled', 'purged', )

  def is_realized(self):
    # XXX
    pass

  def to_aptitude_string(self):
    """
    A string describing a package and a desired state.

    Documented in aptitude(8).
    """

    state = self.attributes['state']
    r = '%(name)s' % self.attributes
    if state in ('installed', 'held', ) \
      and self.attributes['version'] is not None:
        r += '=%(version)s' % self.attributes
    r += {'installed': '+', 'purged': '_',
        'uninstalled': '-', 'held': '=', }[state]
    return r

  def realize(self):
    """
    Install the package.

    Throws in case of failure.
    """

    env2 = dict(os.environ)
    env2['DEBIAN_FRONTEND'] = 'noninteractive'

    subprocess.check_call(
      ['/usr/bin/aptitude', 'install', '-y', '--', self.to_aptitude_string()],
      env=env2)

def register():
  AptitudePackage.register()

