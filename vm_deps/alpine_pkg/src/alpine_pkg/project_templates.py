from __future__ import print_function

import getpass
import os
import string
import sys

from alpine_pkg.project import Dependency
from alpine_pkg.project import Project
from alpine_pkg.project import PROJECT_MANIFEST_FILENAME
from alpine_pkg.project import Person


class ProjectTemplate(Project):

    def __init__(self, alpine_deps=None, system_deps=None, boost_comps=None, **kwargs):
        super(ProjectTemplate, self).__init__(**kwargs)
        self.alpine_deps = alpine_deps or []
        self.system_deps = system_deps or []
        self.boost_comps=boost_comps or []
        self.validate()

    @staticmethod
    def _create_project_template(project_name, description=None, licenses=None,
                                 maintainer_names=None, author_names=None,
                                 version=None, alpine_deps=None, system_deps=None,
                                 boost_comps=None):
        """
        alternative factory method mapping CLI args to argument for
        Project class

        :param project_name:
        :param description:
        :param licenses:
        :param maintainer_names:
        :param authors:
        :param version:
        :param alpine_deps:
        """
        # Sort so they are alphebetical
        licenses = list(licenses or ["TODO"])
        licenses.sort()
        if not maintainer_names:
            maintainer_names = [getpass.getuser()]
        maintainer_names = list(maintainer_names or [])
        maintainer_names.sort()
        maintainers = []
        for maintainer_name in maintainer_names:
            maintainers.append(
                Person(maintainer_name,
                       '%s@todo.todo' % maintainer_name.split()[-1])
            )
        author_names = list(author_names or [])
        author_names.sort()
        authors = []
        for author_name in author_names:
            authors.append(Person(author_name))
        alpine_deps = list(alpine_deps or [])
        alpine_deps.sort()
        pkg_alpine_deps = []
        builddeps=[]
        rundeps=[]
        buildtooldeps=[Dependency('alpine')]
        for dep in alpine_deps:
            if dep.lower() == 'alpine':
                alpine_deps.remove(dep)
                continue
            if dep.lower() == 'genmsg':
                sys.stderr.write('WARNING: Projects with messages or services should not depend on genmsg, but on message_generation and message_runtime\n')
                buildtooldeps.append(Dependency('genmsg'))
                continue
            if dep.lower() == 'message_generation':
                if not 'message_runtime' in alpine_deps:
                    sys.stderr.write('WARNING: Projects with messages or services should depend on both message_generation and message_runtime\n')
                builddeps.append(Dependency('message_generation'))
                continue
            if dep.lower() == 'message_runtime':
                if not 'message_generation' in alpine_deps:
                    sys.stderr.write('WARNING: Projects with messages or services should depend on both message_generation and message_runtime\n')
                rundeps.append(Dependency('message_runtime'))
                continue
            pkg_alpine_deps.append(Dependency(dep))
        for dep in pkg_alpine_deps:
            builddeps.append(dep)
            rundeps.append(dep)
        if boost_comps:
            if not system_deps:
                system_deps = ['boost']
            elif not 'boost' in system_deps:
                system_deps.append('boost')
        for dep in system_deps or []:
            if not dep.lower().startswith('python-'):
                builddeps.append(Dependency(dep))
            rundeps.append(Dependency(dep))
        project_temp = ProjectTemplate(
            name=project_name,
            version=version or '0.0.0',
            description=description or 'The %s project' % project_name,
            buildtooldeps=buildtooldeps,
            builddeps=builddeps,
            rundeps=rundeps,
            alpine_deps=alpine_deps,
            system_deps=system_deps,
            boost_comps=boost_comps,
            licenses=licenses,
            authors=authors,
            maintainers=maintainers,
            urls=[])
        return project_temp


def read_template_file(filename, distro):
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    templates = []
    templates.append(os.path.join(template_dir, distro, '%s.in' % filename))
    templates.append(os.path.join(template_dir, '%s.in' % filename))
    for template in templates:
        if os.path.isfile(template):
            with open(template, 'r') as fhand:
                template_contents = fhand.read()
            return template_contents
    raise IOError(
        "Could not read template for ROS distro "
        "'{}' at '{}': ".format(distro, ', '.join(templates)) +
        "no such file or directory"
    )


def _safe_write_files(newfiles, target_dir):
    """
    writes file contents to target_dir/filepath for all entries of newfiles.
    Aborts early if files exist in places for new files or directories

    :param newfiles: a dict {filepath: contents}
    :param target_dir: a string
    """
    # first check no filename conflict exists
    for filename in newfiles:
        target_file = os.path.join(target_dir, filename)
        if os.path.exists(target_file):
            raise ValueError('File exists: %s' % target_file)
        dirname = os.path.dirname(target_file)
        while(dirname != target_dir):
            if os.path.isfile(dirname):
                raise ValueError('Cannot create directory, file exists: %s' %
                                 dirname)
            dirname = os.path.dirname(dirname)

    for filename, content in newfiles.items():
        target_file = os.path.join(target_dir, filename)
        dirname = os.path.dirname(target_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        # print(target_file, content)
        with open(target_file, 'ab') as fhand:
            fhand.write(content.encode())
        print('Created file %s' % os.path.relpath(target_file, os.path.dirname(target_dir)))


def create_project_files(target_path, project_template, distro,
                         newfiles=None):
    """
    creates several files from templates to start a new project.

    :param target_path: parent folder where to create the project
    :param project_template: contains the required information
    :param distro: name of the distro to look up respective template
    :param newfiles: dict {filepath: contents} for additional files to write
    """
    if newfiles is None:
        newfiles = {}
    # allow to replace default templates when path string is equal
    manifest_path = os.path.join(target_path, PROJECT_MANIFEST_FILENAME)
    if manifest_path not in newfiles:
        newfiles[manifest_path] = \
            create_project_xml(project_template, distro)
    cmake_path = os.path.join(target_path, 'CMakeLists.txt')
    if not cmake_path in newfiles:
        newfiles[cmake_path] = create_cmakelists(project_template, distro)
    _safe_write_files(newfiles, target_path)
    if 'cpp' in project_template.alpine_deps:
        fname = os.path.join(target_path, 'include', project_template.name)
        os.makedirs(fname)
        print('Created folder %s' % os.path.relpath(fname, os.path.dirname(target_path)))
    if 'cpp' in project_template.alpine_deps or \
            'py' in project_template.alpine_deps:
        fname = os.path.join(target_path, 'src')
        os.makedirs(fname)
        print('Created folder %s' % os.path.relpath(fname, os.path.dirname(target_path)))


class AlpineTemplate(string.Template):
    """subclass to use @ instead of $ as markers"""
    delimiter = '@'
    escape = '@'


def create_cmakelists(project_template, distro):
    """
    :param project_template: contains the required information
    :returns: file contents as string
    """
    cmakelists_txt_template = read_template_file('CMakeLists.txt', distro)
    ctemp = AlpineTemplate(cmakelists_txt_template)
    if project_template.alpine_deps == []:
        components = ''
    else:
        components = ' COMPONENTS\n  %s\n' % '\n  '.join(project_template.alpine_deps)
    has_include_folder = 'cpp' in project_template.alpine_deps
    boost_find_package = \
        ('' if not project_template.boost_comps
         else ('find_package(Boost REQUIRED COMPONENTS %s)\n' %
               ' '.join(project_template.boost_comps)))
    system_find_package = ''
    for sysdep in project_template.system_deps:
        if sysdep == 'boost':
            continue
        if sysdep.startswith('python-'):
            system_find_package += '# '
        system_find_package += 'find_package(%s REQUIRED)\n' % sysdep
    # provide dummy values
    alpine_depends = (' '.join(project_template.alpine_deps)
                      if project_template.alpine_deps
                      else 'other_alpine_pkg')
    system_depends = (' '.join(project_template.system_deps)
                      if project_template.system_deps
                      else 'system_lib')
    message_pkgs = [pkg for pkg in project_template.alpine_deps if pkg.endswith('_msgs')]
    if message_pkgs:
        message_depends = '#   %s' % '#   '.join(message_pkgs)
    else:
        message_depends = '#   std_msgs  # Or other projects containing msgs'
    temp_dict = {'name': project_template.name,
                 'components': components,
                 'include_directories': _create_include_macro(project_template),
                 'boost_find': boost_find_package,
                 'systems_find': system_find_package,
                 'alpine_depends': alpine_depends,
                 'system_depends': system_depends,
                 'target_libraries': _create_targetlib_args(project_template),
                 'message_dependencies': message_depends
                 }
    return ctemp.substitute(temp_dict)


def _create_targetlib_args(project_template):
    result = '#   ${alpine_LIBRARIES}\n'
    if project_template.boost_comps:
        result += '#   ${Boost_LIBRARIES}\n'
    if project_template.system_deps:
        result += (''.join(
                ['#   ${%s_LIBRARIES}\n' %
                 sdep for sdep in project_template.system_deps]))
    return result


def _create_include_macro(project_template):
    result = '# include_directories(include)'
    includes = []
    if project_template.alpine_deps:
        includes.append('${alpine_INCLUDE_DIRS}')
    if project_template.boost_comps:
        includes.append('${Boost_INCLUDE_DIRS}')
    if project_template.system_deps:
        deplist = []
        for sysdep in project_template.system_deps:
            if not sysdep.startswith('python-'):
                deplist.append(sysdep)
                includes.append('${%s_INCLUDE_DIRS}' % sysdep)
        if deplist:
            result += '\n# TODO: Check names of system library include directories (%s)' % ', '.join(deplist)
    if includes:
        result += '\ninclude_directories(\n  %s\n)' % '\n  '.join(includes)
    return result


def _create_depend_tag(dep_type,
                       name,
                       eq=None,
                       lt=None,
                       lte=None,
                       gt=None,
                       gte=None):
    """
    Helper to create xml snippet for project.xml
    """

    version_string = []
    for key, var in {'eq': eq,
                     'lt': lt,
                     'lte': lte,
                     'gt': gt,
                     'gte': gte}.items():
        if var is not None:
            version_string.append(' %s="%s"' % (key, var))
    result = '  <%s%s>%s</%s>\n' % (dep_type,
                                  ''.join(version_string),
                                  name,
                                  dep_type)
    return result


def create_project_xml(project_template, distro):
    """
    :param project_template: contains the required information
    :returns: file contents as string
    """
    project_xml_template = \
        read_template_file(PROJECT_MANIFEST_FILENAME, distro)
    ctemp = AlpineTemplate(project_xml_template)
    temp_dict = {}
    for key in project_template.__slots__:
        temp_dict[key] = getattr(project_template, key)

    if project_template.abi:
        temp_dict['abi'] = ' abi="%s"' % project_template.abi
    else:
        temp_dict['abi'] = ''

    if not project_template.description:
        temp_dict['description'] = 'The %s project ...' % project_template.name

    licenses = []
    for plicense in project_template.licenses:
        licenses.append('  <license>%s</license>\n' % plicense)
    temp_dict['licenses'] = ''.join(licenses)

    def get_person_tag(tagname, person):
        email_string = (
            "" if person.email is None else 'email="%s"' % person.email
        )
        return '  <%s %s>%s</%s>\n' % (tagname, email_string,
                                       person.name, tagname)

    maintainers = []
    for maintainer in project_template.maintainers:
        maintainers.append(get_person_tag('maintainer', maintainer))
    temp_dict['maintainers'] = ''.join(maintainers)

    urls = []
    for url in project_template.urls:
        type_string = ("" if url.type is None
                       else 'type="%s"' % url.type)
        urls.append('    <url %s >%s</url>\n' % (type_string, url.url))
    temp_dict['urls'] = ''.join(urls)

    authors = []
    for author in project_template.authors:
        authors.append(get_person_tag('author', author))
    temp_dict['authors'] = ''.join(authors)

    dependencies = []
    dep_map = {
        'builddep': project_template.builddeps,
        'buildtooldep': project_template.buildtooldeps,
        'rundep': project_template.rundeps,
        'testdep': project_template.testdeps,
        'conflict': project_template.conflicts,
        'replace': project_template.replaces
    }
    for dep_type in ['buildtooldep', 'builddep', 'rundep',
                     'testdep', 'conflict', 'replace']:
        for dep in sorted(dep_map[dep_type], key=lambda x: x.name):
            if 'depend' in dep_type:
                dep_tag = _create_depend_tag(
                    dep_type,
                    dep.name,
                    dep.eq,
                    dep.lt,
                    dep.lte,
                    dep.gt,
                    dep.gte
                    )
                dependencies.append(dep_tag)
            else:
                dependencies.append(_create_depend_tag(dep_type,
                                                       dep.name))
    temp_dict['dependencies'] = ''.join(dependencies)

    exports = []
    if project_template.exports is not None:
        for export in project_template.exports:
            if export.content is not None:
                print('WARNING: Create project does not know how to '
                      'serialize exports with content: '
                      '%s, %s, ' % (export.tagname, export.attributes) +
                      '%s' % (export.content),
                      file=sys.stderr)
            else:
                attribs = [' %s="%s"' % (k, v) for (k, v) in export.attributes.items()]
                line = '    <%s%s/>\n' % (export.tagname, ''.join(attribs))
                exports.append(line)
    temp_dict['exports'] = ''.join(exports)

    temp_dict['components'] = project_template.alpine_deps

    return ctemp.substitute(temp_dict)
