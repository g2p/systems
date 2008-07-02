
import re
import subprocess

from registry import Registry
import resource

__all__ = ('AptitudePackage', )

class AptitudePackage(resource.Resource):
  """
  A debian package, managed by aptitude

  Dependencies are not managed here.
  """

  @classmethod
  def register(cls):
    cls.__restype = resource.ResourceType('AptitudePackage', cls,
      [
      resource.ResourceAttr('name',
        identifying=True, naming=True),
      resource.ResourceAttr('version',
        identifying=False, naming=False, default_to_none=True),
      resource.ResourceAttr('state',
        identifying=False, naming=False, default_value='installed'),
    ])
    Registry.get_singleton().register_resource_type(cls.__restype)

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

  def _set_valdict(self, valdict):
    """
    Extra checks.
    """

    if not self.is_valid_pkgname(valdict['name']):
      raise ValueError('Not a valid package name')
    if not self.is_valid_version(valdict['version']):
      raise ValueError('Not a valid package version')
    if not self.is_valid_state(valdict['state']):
      raise ValueError('Not a valid package state')
    super(AptitudePackage, self)._set_valdict(valdict)

  def is_realized(self):
    # XXX
    pass

  def to_aptitude_string(self):
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

    subprocess.check_call(
      ['/usr/bin/aptitude', 'install', self.to_aptitude_string()],
      env={'DEBIAN_FRONTEND': 'noninteractive'})

AptitudePackage.register()

# vim: set sw=2 ts=2 et :
