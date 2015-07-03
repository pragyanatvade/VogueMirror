from __future__ import print_function
import datetime
import docutils.core
import os
import re

from alpine_pkg.changelog_generator import FORTHCOMING_LABEL


def _replace_version(project_str, new_version):
    """
    replaces the version tag in contents if there is only one instance

    :param project_str: str contents of project.xml
    :param new_version: str version number
    :returns: str new project.xml
    :raises RuntimeError:
    """
    # try to replace contens
    new_project_str, number_of_subs = re.subn('<version([^<>]*)>[^<>]*</version>', '<version\g<1>>%s</version>' % new_version, project_str)
    if number_of_subs != 1:
        raise RuntimeError('Illegal number of version tags: %s' % (number_of_subs))
    return new_project_str


def _check_for_version_comment(project_str, new_version):
    """
    checks if a comment is present behind the version tag and return it

    :param project_str: str contents of project.xml
    :param version: str version number
    :returns: str comment if available, else None
    """
    version_tag = '>%s</version>' % new_version
    pattern = '%s[ \t]*%s *(.+) *%s' % (re.escape(version_tag), re.escape('<!--'), re.escape('-->'))
    comment = re.search(pattern, project_str)
    if comment:
        comment = comment.group(1)
    return comment


def update_versions(paths, new_version):
    """
    bulk replace of version: searches for project.xml files directly in given folders and replaces version tag within.

    :param paths: list of string, folder names
    :param new_version: version string "int.int.int"
    :raises RuntimeError: if any one project.xml cannot be updated
    """
    files = {}
    for path in paths:
        project_path = os.path.join(path, 'project.xml')
        with open(project_path, 'r') as f:
            project_str = f.read()
        try:
            new_project_str = _replace_version(project_str, new_version)
            comment = _check_for_version_comment(new_project_str, new_version)
            if comment:
                print('NOTE: The project manifest "%s" contains a comment besides the version tag:\n  %s' % (path, comment))
        except RuntimeError as rue:
            raise RuntimeError('Could not bump version number in file %s: %s' % (project_path, str(rue)))
        files[project_path] = new_project_str
    # if all replacements successful, write back modified project.xml
    for project_path, new_project_str in files.items():
        with open(project_path, 'w') as f:
            f.write(new_project_str)


def get_forthcoming_label(rst):
    document = docutils.core.publish_doctree(rst)
    forthcoming_label = None
    for child in document.children:
        title = None
        if isinstance(child, docutils.nodes.subtitle):
            title = child
        elif isinstance(child, docutils.nodes.section):
            section = child
            if len(section.children) > 0 and isinstance(section.children[0], docutils.nodes.title):
                title = section.children[0]
        if title and len(title.children) > 0 and isinstance(title.children[0], docutils.nodes.Text):
            title_text = title.children[0].rawsource
            if FORTHCOMING_LABEL.lower() in title_text.lower():
                if forthcoming_label:
                    raise RuntimeError('Found multiple forthcoming sections')
                forthcoming_label = title_text
    return forthcoming_label


def update_changelog_sections(changelogs, new_version):
    # rename forthcoming sections to new_version including current date
    new_changelog_data = {}
    new_label = '%s (%s)' % (new_version, datetime.date.today().isoformat())
    for pkg_name, (changelog_path, changelog, forthcoming_label) in changelogs.items():
        data = rename_section(changelog.rst, forthcoming_label, new_label)
        new_changelog_data[changelog_path] = data

    for changelog_path, data in new_changelog_data.items():
        with open(changelog_path, 'w') as f:
            f.write(data)


def rename_section(data, old_label, new_label):
    valid_section_characters = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    def replace_section(match):
        section_char = match.group(2)[0]
        return new_label + '\n' + section_char * len(new_label)
    pattern = '^(' + re.escape(old_label) + ')\n([' + re.escape(valid_section_characters) + ']+)$'
    data, count = re.subn(pattern, replace_section, data, flags=re.MULTILINE)
    if count == 0:
        raise RuntimeError('Could not find section')
    if count > 1:
        raise RuntimeError('Found multiple matching sections')
    return data
