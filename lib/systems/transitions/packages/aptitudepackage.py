# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import re

from systems.collector import Collector, Aggregate, CResource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType
from systems.dsl import transition

__all__ = ('register', )


class AptitudePackage(CResource):
  """
  A debian package, managed by aptitude.

  Package dependencies are not managed here.
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('AptitudePackage', cls,
        id_type={
          'name': AttrType(
            pytype=str,
            valid_condition=cls.is_valid_pkgname),
          },
        state_type={
          'version': AttrType(
            none_allowed=True,
            pytype=str,
            valid_condition=cls.is_valid_version),
          'state': AttrType(
            default_value='installed',
            pytype=str,
            valid_condition=cls.is_valid_state),
          },
        )
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_pkgname(cls, name):
    # Specified here:
    # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Package
    return bool(re.match('^[a-z][a-z0-9+\.-]*[a-z0-9]$', name))

  @classmethod
  def is_valid_version(cls, version):
    # From lintian's _valid_version
    # XXX can pass dashes. Check in aptitude source code if it matches.
    # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
    return bool(
        re.match('^(\d+:)?([-\.+:~a-z0-9]+?)(-[\.+~a-z0-9]+)?$', version))

  @classmethod
  def is_valid_state(cls, state):
    # Semantics for held are unclear. Disable hold support.
    # A package can be held installed or held removed.
    # Installing and holding can't be done in a single aptitude call.
    return state in ('installed', 'uninstalled', 'purged', )

  def to_aptitude_string(self):
    """
    A string describing a package and a desired state.

    Documented in aptitude(8).
    """

    state = self.wanted_attrs['state']
    version = self.wanted_attrs['version']
    r = '%(name)s' % self.id_attrs
    if state in ('installed', 'held', ) and version is not None:
      r += '=' + version
    r += {'installed': '+', 'purged': '_',
        'uninstalled': '-', 'held': '=', }[state]
    return r


class AptitudePackages(Aggregate):
  def __init__(self, packages):
    super(AptitudePackages, self).__init__()
    self.__packages = packages

  def to_aptitude_list(self):
    """
    A string describing a package and a desired state.

    Documented in aptitude(8).
    """

    return [p.to_aptitude_string() for p in self.__packages]

  def expand_into(self, rg):
    cmdline = ['/usr/bin/aptitude', 'install', '-y', '--', ]
    cmdline.extend(self.to_aptitude_list())
    cmd = transition('Command',
        extra_env={ 'DEBIAN_FRONTEND': 'noninteractive', },
        cmdline=cmdline)
    rg.add_transition(cmd)


class AptitudePackageCollector(Collector):
  """
  Group several aptitude package operations into one.
  """

  def filter(self, collectible):
    return isinstance(collectible, AptitudePackage)

  def collect(self, transitions):
    return AptitudePackages(transitions)

  @classmethod
  def register(cls):
    Registry.get_singleton().collectors \
        .register(cls('AptitudePackageCollector'))

def register():
  AptitudePackage.register()
  AptitudePackageCollector.register()

