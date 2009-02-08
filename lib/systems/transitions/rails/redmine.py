# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


class Redmine(EResource):
  """
  A redmine instance.
  """

  def expand_into(self, rg):
    svn_branch = self.wanted_attrs['svn_branch']
    cluster_ref = self.wanted_attrs['cluster']
    rails_name = 'redmine-%s' % self.id_attrs['name']
    # Privileged (create tables, update checkout)
    maint_user_name = 'redmine-maint-%s' % self.id_attrs['name']
    # Less privileged (run server, write temporary files)
    run_user_name = 'redmine-run-%s' % self.id_attrs['name']

    run_user = rg.add_resource(resource('User', name=run_user_name))
    maint_user = rg.add_resource(resource('User', name=maint_user_name))
    run_user_ref = run_user.ref(rg)
    maint_user_ref = maint_user.ref(rg)
    loc = rg.add_resource(resource('Directory',
        path=self.id_attrs['path'],
        owner=maint_user_name,
        group='root',
        mode='0755',
        ),
      depends=(maint_user, ))
    loc_ref = loc.ref(rg)
    co = rg.add_resource(resource('SvnWorkingCopy',
        location=loc_ref,
        url=svn_branch,
        ))
    loc_ref = rg.make_ref(loc, depends=(co, ))
    rails = rg.add_resource(resource('Rails',
        name=rails_name,
        location=loc_ref,
        maint_user=maint_user_ref,
        run_user=run_user_ref,
        cluster=cluster_ref,
        ))


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
  get_registry().resource_types.register(restype)


