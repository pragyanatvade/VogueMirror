from __future__ import print_function

import copy
import sys

from alpine_pkg.projects import find_projects


class _ProjectDecorator(object):

    def __init__(self, project, path):
        self.project = project
        self.path = path
        self.is_metaproject = 'metaproject' in [e.tagname for e in self.project.exports]
        message_generators = [e.content for e in self.project.exports if e.tagname == 'message_generator']
        self.message_generator = message_generators[0] if message_generators else None
        # full includes direct build depends and recursive rundeps of these builddeps
        self.depends_for_topological_order = None

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self.project, name)

    def calculate_depends_for_topological_order(self, projects):
        """
        Sets self.depends_for_topological_order to the recursive
        dependencies required for topological order. It contains all
        direct build- and buildtool dependencies and their recursive
        runtime dependencies. The set only contains projects which
        are in the passed projects dictionary.

        :param projects: dict of name to ``_ProjectDecorator``
        """
        self.depends_for_topological_order = set([])
        # skip external dependencies, meaning names that are not known projects
        for name in [d.name for d in (self.project.builddeps + self.project.buildtooldeps) if d.name in projects.keys()]:
            if not self.is_metaproject and projects[name].is_metaproject:
                print('WARNING: project "%s" should not depend on metaproject "%s" but on its projects instead' % (self.name, name), file=sys.stderr)
            projects[name]._add_recursive_rundeps(projects, self.depends_for_topological_order)

    def _add_recursive_rundeps(self, projects, depends_for_topological_order):
        """
        Modifies depends_for_topological_order argument by adding
        rundeps of self recursively. Only projects which are in
        the passed projects are added and recursed into.

        :param projects: dict of name to ``_ProjectDecorator``
        :param depends_for_topological_order: set to be extended
        """
        depends_for_topological_order.add(self.project.name)
        project_names = projects.keys()
        for name in [d.name for d in self.project.rundeps if d.name in project_names and d.name not in depends_for_topological_order]:
            projects[name]._add_recursive_rundeps(projects, depends_for_topological_order)


def topological_order(root_dir, whitelisted=None, blacklisted=None, underlay_workspaces=None):
    '''
    Crawls the filesystem to find projects and uses their
    dependencies to return a topologically order list.

    :param root_dir: The path to search in, ``str``
    :param whitelisted: A list of whitelisted project names, ``list``
    :param blacklisted: A list of blacklisted project names, ``list``
    :param underlay_workspaces: A list of underlay workspaces of projects which might provide dependencies in case of partial workspaces, ``list``
    :returns: A list of tuples containing the relative path and a ``Project`` object, ``list``
    '''
    projects = find_projects(root_dir)
    # find projects in underlayed workspaces
    underlay_workspaces = {}
    if underlay_workspaces:
        for workspace in reversed(underlay_workspaces):
            for path, project in find_projects(workspace).items():
                underlay_projects[project.name] = (path, project)

    return topological_order_projects(projects, whitelisted, blacklisted, underlay_projects=dict(underlay_projects.values()))


def topological_order_projects(projects, whitelisted=None, blacklisted=None, underlay_projects=None):
    '''
    Topologically orders projects.
    First returning projects which have message generators and then
    the rest based on direct build-/buildtooldeps and indirect
    recursive rundeps.

    :param projects: A dict mapping relative paths to ``Project`` objects ``dict``
    :param whitelisted: A list of whitelisted project names, ``list``
    :param blacklisted: A list of blacklisted project names, ``list``
    :param underlay_projects: A dict mapping relative paths to ``Project`` objects ``dict``
    :returns: A list of tuples containing the relative path and a ``Project`` object, ``list``
    '''
    decorators_by_name = {}
    for path, project in projects.items():
        # skip non-whitelisted projects
        if whitelisted and project.name not in whitelisted:
            continue
        # skip blacklisted projects
        if blacklisted and project.name in blacklisted:
            continue
        projects_with_same_name = [p for p in decorators_by_name.values() if p.name == project.name]
        if projects_with_same_name:
            path_with_same_name = [p for p, v in projects.items() if v == projects_with_same_name[0]]
            raise RuntimeError('Two projects with the same name "%s" in the workspace:\n- %s\n- %s' % (project.name, path_with_same_name[0], path))
        decorators_by_name[project.name] = _ProjectDecorator(project, path)

    underlay_decorators_by_name = {}
    if underlay_projects:
        for path, project in underlay_projects.items():
            # skip overlayed projects
            if project.name in decorators_by_name:
                continue
            underlay_decorators_by_name[project.name] = _ProjectDecorator(project, path)
        decorators_by_name.update(underlay_decorators_by_name)

    # calculate transitive dependencies
    for decorator in decorators_by_name.values():
        decorator.calculate_depends_for_topological_order(decorators_by_name)

    tuples = _sort_decorated_projects(decorators_by_name)
    # remove underlay projects from result
    # 
    return [(path, project) for path, project in tuples if project.name not in underlay_decorators_by_name]


def _reduce_cycle_set(projects_orig):
    '''
    This function iteratively removes some projects from a set that are definitely not part of any cycle.

    When there is a cycle in the project dependencies,
    _sort_decorated_projects only knows the set of projects containing
    the cycle.
    :param projects: A dict mapping project name to ``_ProjectDecorator`` objects ``dict``
    :returns: A list of project names from the input which could not easily be detected as not being part of a cycle.
    '''
    assert(projects_orig)
    projects = copy.copy(projects_orig)
    last_depended = None
    while len(projects) > 0:
        depended = set([])
        for name, decorator in projects.items():
            if decorator.depends_for_topological_order:
                depended = depended.union(decorator.depends_for_topological_order)
        for name in list(projects.keys()):
            if not name in depended:
                del projects[name]
        if last_depended:
            if last_depended == depended:
                return projects.keys()
        last_depended = depended


def _sort_decorated_projects(projects_orig):
    '''
    Sorts projects according to dependency ordering,
    first considering the message generators and their recursive dependencies
    and then the rest of the projects.

    When a circle is detected, a tuple with None and a string giving a
    superset of the guilty projects.

    :param projects: A dict mapping project name to ``_ProjectDecorator`` objects ``dict``
    :returns: A List of tuples containing the relative path and a ``Project`` object ``list``
    '''
    projects = copy.deepcopy(projects_orig)

    # mark all projects which are (recursively) dependent on by message generators
    dependency_names_to_follow = set([name for name, decorator in projects.items() if decorator.message_generator])
    not_marked_project_names = set(projects.keys()) - dependency_names_to_follow
    while dependency_names_to_follow:
        pkg_name = dependency_names_to_follow.pop()
        for name in projects[pkg_name].depends_for_topological_order:
            if name in not_marked_project_names:
                # mark project
                projects[name].message_generator = True
                not_marked_project_names.remove(name)
                # queue for recursion
                dependency_names_to_follow.add(name)

    ordered_projects = []
    while len(projects) > 0:
        # find all projects without build dependencies
        message_generators = []
        non_message_generators = []
        for name, decorator in projects.items():
            if not decorator.depends_for_topological_order:
                if decorator.message_generator:
                    message_generators.append(name)
                else:
                    non_message_generators.append(name)
        # first choose message generators
        if message_generators:
            names = message_generators
        elif non_message_generators:
            names = non_message_generators
        else:
            # in case of a circular dependency pass a string with
            # the names list of remaining project names, with path
            # None to indicate cycle
            ordered_projects.append([None, ', '.join(sorted(_reduce_cycle_set(projects)))])
            break

        # alphabetic order only for convenience
        names.sort()

        # add first candidates to ordered list
        # do not add all candidates since removing the depends from the first might affect the next candidates
        name = names[0]
        ordered_projects.append([projects[name].path, projects[name].project])
        # remove project from further processing
        del projects[name]
        for project in projects.values():
            if name in project.depends_for_topological_order:
                project.depends_for_topological_order.remove(name)
    return ordered_projects
