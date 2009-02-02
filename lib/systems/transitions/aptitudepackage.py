# vim: set fileencoding=utf-8 sw=2 ts=2 et :
import re
import os
import subprocess

from systems.collector import Collector, Aggregate
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.dsl import transition

__all__ = ('register', )


class AptitudePackage(Resource):
  """
  A debian package, managed by aptitude.

  Package dependencies are not managed here.
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('AptitudePackage', cls,
        id_type={
          'name': AttrType(
            valid_condition=cls.is_valid_pkgname),
          },
        state_type={
          'version': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_version),
          'state': AttrType(
            default_value='installed',
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
    if version is None:
      return True
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
    r = '%(name)s' % self.id_attrs
    if state in ('installed', 'held', ) \
      and self.wanted_attrs['version'] is not None:
        r += '=%(version)s' % self.attributes
    r += {'installed': '+', 'purged': '_',
        'uninstalled': '-', 'held': '=', }[state]
    return r

  def place_transitions(self, transition_graph):
    return AptitudePackages([self]).place_transitions(transition_graph)


class AptitudePackages(Aggregate):
  def __init__(self, packages):
    self.__packages = packages

  def to_aptitude_list(self):
    """
    A string describing a package and a desired state.

    Documented in aptitude(8).
    """

    return [p.to_aptitude_string() for p in self.__packages]

  def place_transitions(self, transition_graph):
    cmdline=['/usr/bin/aptitude', 'install', '-y', '--', ]
    cmdline.extend(self.to_aptitude_list())
    cmd = transition('Command',
        extra_env={ 'DEBIAN_FRONTEND': 'noninteractive', },
        cmdline=cmdline)
    transition_graph.add_transition(cmd)
    return cmd


class AptitudePackageCollector(Collector):
  """
  Group several aptitude package operations into one.
  """

  def filter(self, transition):
    return isinstance(transition, AptitudePackage)

  def collect(self, transitions):
    return AptitudePackages(transitions)

  @classmethod
  def register(cls):
    Registry.get_singleton().collectors \
        .register(cls('AptitudePackageCollector'))

def register():
  AptitudePackage.register()
  AptitudePackageCollector.register()

