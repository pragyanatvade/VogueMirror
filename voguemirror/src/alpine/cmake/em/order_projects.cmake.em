# generated from alpine/cmake/em/order_projects.cmake.em
@{
import os
try:
    from alpine_pkg.cmake import get_metaproject_cmake_template_path
except ImportError as e:
    raise RuntimeError('ImportError: "from alpine_pkg.cmake import get_metaproject_cmake_template_path" failed: %s\nMake sure that you have installed "alpine_pkg", it is up to date and on the PYTHONPATH.' % e)
try:
    from alpine_pkg.topological_order import topological_order
except ImportError as e:
    raise RuntimeError('ImportError: "from alpine_pkg.topological_order import topological_order" failed: %s\nMake sure that you have installed "alpine_pkg", it is up to date and on the PYTHONPATH.' % e)
try:
    from alpine_pkg.project import InvalidProject
except ImportError as e:
    raise RuntimeError('ImportError: "from alpine_pkg.project import InvalidProject" failed: %s\nMake sure that you have installed "alpine_pkg", it is up to date and on the PYTHONPATH.' % e)
# vars defined in order_projects.context.py.in
try:
    ordered_projects = topological_order(os.path.normpath(source_root_dir), whitelisted=whitelisted_projects, blacklisted=blacklisted_projects, underlay_workspaces=underlay_workspaces)
except InvalidProject as e:
    print('message(FATAL_ERROR "%s")' % e)
    ordered_projects = []
fatal_error = False
}@

set(ALPINE_ORDERED_PROJECTS "")
set(ALPINE_ORDERED_PROJECT_PATHS "")
set(ALPINE_ORDERED_PROJECTS_IS_META "")
set(ALPINE_ORDERED_PROJECTS_BUILD_TYPE "")
@[for path, project in ordered_projects]@
@[if path is None]@
message(FATAL_ERROR "Circular dependency in subset of projects:\n@project")
@{
fatal_error = True
}@
@[elif project.name != 'alpine']@
list(APPEND ALPINE_ORDERED_PROJECTS "@(project.name)")
list(APPEND ALPINE_ORDERED_PROJECT_PATHS "@(path.replace('\\','/'))")
list(APPEND ALPINE_ORDERED_PROJECTS_IS_META "@(str('metaproject' in [e.tagname for e in project.exports]))")
list(APPEND ALPINE_ORDERED_PROJECTS_BUILD_TYPE "@(str([e.content for e in project.exports if e.tagname == 'build_type'][0]) if 'build_type' in [e.tagname for e in project.exports] else 'alpine')")
@{
deprecated = [e for e in project.exports if e.tagname == 'deprecated']
}@
@[if deprecated]@
message("WARNING: Project '@(project.name)' is deprecated@(' (%s)' % deprecated[0].content if deprecated[0].content else '')")
@[end if]@
@[end if]@
@[end for]@

@[if not fatal_error]@
@{
message_generators = [project.name for (_, project) in ordered_projects if 'message_generator' in [e.tagname for e in project.exports]]
}@
set(ALPINE_MESSAGE_GENERATORS @(' '.join(message_generators)))
@[end if]@

set(ALPINE_METAPROJECT_CMAKE_TEMPLATE "@(get_metaproject_cmake_template_path().replace('\\','/'))")
