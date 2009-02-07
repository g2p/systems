# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


class Redmine(EResource):
  """
  A redmine instance.
  """

  def expand_into(self, rg):
    svn_branch = self.wanted_attrs['svn_branch']
    cluster_ref = rg.refs_received['cluster']
    rails_name = 'redmine-%s' % self.id_attrs['name']
    # Privileged (create tables, update checkout)
    maint_user_name = 'redmine-maint-%s' % self.id_attrs['name']
    # Less privileged (run server, write temporary files)
    run_user_name = 'redmine-run-%s' % self.id_attrs['name']

    run_user = rg.add_resource(resource('User', name=run_user_name))
    maint_user = rg.add_resource(resource('User', name=maint_user_name))
    loc = rg.add_resource(resource('Directory',
        path=self.id_attrs['path'],
        owner=maint_user_name,
        group='root',
        mode='0755',
        ),
      depends=(maint_user, ))
    co = rg.add_resource(resource('SvnWorkingCopy',
        location=loc,
        url=svn_branch,
        ))
    rails = rg.add_resource(resource('Rails',
        name=rails_name,
        location=loc,
        maint_user=maint_user,
        run_user=run_user,
        cluster=cluster_ref,
        ))
    rg.add_dependency(co, rg.refs_passed(rails)['location'])


def register():
  restype = ResourceType('Redmine', Redmine,
    id_type={
      # They must be _separately_ unique.
      'path': AttrType(
        pytype=str),
      'name': AttrType(
        pytype=str),
      },
    state_type={
      'svn_branch': AttrType(
        default_value='http://redmine.rubyforge.org/svn/branches/0.8-stable/',
        pytype=str),
      'cluster': RefAttrType(
        rtype='PgCluster'),
      })
  Registry.get_singleton().resource_types.register(restype)


