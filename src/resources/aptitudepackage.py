
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
      resource.ResourceAttr('version', True, False),
    ])

  def __init__(self, name, version=None, graph=None):
    """
    Constructor.

    graph is the container resource graph.
    """

    # I could use kargs but that wouldn't be self-documenting
    valdict = {'name': name, 'version': version, }
    resource.Resource.__init__(self,
        type=self.resource_type, valdict=valdict, graph=graph)
    self.check_attrs() #XXX has already been added to graph

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

  def check_attrs(self):
    if not self.is_valid_pkgname(self.attributes['name']):
      raise ValueError('Not a valid package name')
    if not self.is_valid_version(self.attributes['version']):
      raise ValueError('Not a valid package version')

  def realize(self):
    """
    Install the package.

    Throws in case of failure.
    """

    if self.attributes['version'] is None:
      pkgatvers = '%(name)s' % self.attributes
    else:
      pkgatvers = '%(name)s=%(version)s' % self.attributes
    subprocess.check_call(['/usr/bin/aptitude', 'install', pkgatvers])


# vim: set sw=2 ts=2 et :
