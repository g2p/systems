
import re
import subprocess

import resource

__all__ = ('AptitudePackage', )

class AptitudePackage(resource.Resource):
  """
  A debian package, managed by aptitude

  Dependencies are not managed here.
  """

  resource_type = resource.ResourceType('AptitutePackage', [
      resource.ResourceAttr('name', True, True),
      resource.ResourceAttr('version', False, False),
      resource.ResourceAttr('state', False, False),
    ])

  def __init__(self, name, version=None, state='installed', graph=None):
    """
    Constructor.

    graph is the container resource graph.
    """

    # I could use kargs but that wouldn't be self-documenting
    valdict = {'name': name, 'version': version, 'state': state}
    self.check_attrs(valdict)

    resource.Resource.__init__(self,
        type=self.resource_type, valdict=valdict, graph=graph)

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
    # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
    return bool(
        re.match('^(\d+:)?([-\.+:~a-z0-9]+?)(-[\.+~a-z0-9]+)?$', version))

  @classmethod
  def is_valid_state(cls, state):
    # Semantics for held are unclear. Disable hold support.
    # A package can be held installed or held removed.
    # Installing and holding can't be done in a single aptitude call.
    return state in ('installed', 'uninstalled', 'purged', )

  @classmethod
  def check_attrs(cls, valdict):
    if not cls.is_valid_pkgname(valdict['name']):
      raise ValueError('Not a valid package name')
    if not cls.is_valid_version(valdict['version']):
      raise ValueError('Not a valid package version')
    if not cls.is_valid_state(valdict['state']):
      raise ValueError('Not a valid package state')

  def is_realized(self):
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


# vim: set sw=2 ts=2 et :
