"""
Library for providing the relevant information from the project
manifest for the Python setup.py file.
"""

from __future__ import print_function

import os
import sys

from alpine_pkg.project import InvalidProject, parse_project


def generate_distutils_setup(project_xml_path=os.path.curdir, **kwargs):
    """
    Extract the information relevant for distutils from the package
    manifest. The following keys will be set:

    The "name" and "version" are taken from the eponymous tags.

    A single maintainer will set the keys "maintainer" and
    "maintainer_email" while multiple maintainers are merged into the
    "maintainer" fields (including their emails). Authors are handled
    likewise.

    The first URL of type "website" (or without a type) is used for
    the "url" field.

    The "description" is taken from the eponymous tag if it does not
    exceed 200 characters. If it does "description" contains the
    truncated text while "description_long" contains the complete.

    All licenses are merged into the "license" field.

    :param kwargs: All keyword arguments are passed through. The
    above mentioned keys are verified to be identical if passed as
    a keyword argument

    :returns: return dict populated with parsed fields and passed
    keyword arguments
    :raises: :exc:`InvalidProject`
    :raises: :exc:`IOError`
    """
    project = parse_project(project_xml_path)

    data = {}
    data['name'] = project.name
    data['version'] = project.version

    # either set one author with one email or join all in a single field
    if len(project.authors) == 1 and project.authors[0].email is not None:
        data['author'] = project.authors[0].name
        data['author_email'] = project.authors[0].email
    else:
        data['author'] = ', '.join([('%s <%s>' % (a.name, a.email) if a.email is not None else a.name) for a in project.authors])

    # either set one maintainer with one email or join all in a single field
    if len(project.maintainers) == 1:
        data['maintainer'] = project.maintainers[0].name
        data['maintainer_email'] = project.maintainers[0].email
    else:
        data['maintainer'] = ', '.join(['%s <%s>' % (m.name, m.email) for m in project.maintainers])

    # either set the first URL with the type 'website' or the first URL of any type
    websites = [url.url for url in project.urls if url.type == 'website']
    if websites:
        data['url'] = websites[0]
    elif project.urls:
        data['url'] = project.urls[0].url

    if len(project.description) <= 200:
        data['description'] = project.description
    else:
        data['description'] = project.description[:197] + '...'
        data['long_description'] = project.description

    data['license'] = ', '.join(project.licenses)

    # pass keyword arguments and verify equality if generated and passed in
    for k, v in kwargs.items():
        if k in data:
            if v != data[k]:
                raise InvalidProject('The keyword argument "%s" does not match the information from project.xml: "%s" != "%s"' % (k, v, data[k]))
        else:
            data[k] = v

    return data


def get_global_bin_destination():
    return 'bin'


def get_global_etc_destination():
    return 'etc'


def get_global_include_destination():
    return 'include'


def get_global_lib_destination():
    return 'lib'


def get_global_libexec_destination():
    return 'lib'


def get_global_python_destination():
    dest = 'lib/python%u.%u/' % (sys.version_info[0], sys.version_info[1])
    if '--install-layout=deb' not in sys.argv[1:]:
        dest += 'site-packages'
    else:
        dest += 'dist-packages'
    return dest


def get_global_share_destination():
    return 'share'


def get_project_bin_destination(pkgname):
    return os.path.join(get_global_libexec_destination(), pkgname)


def get_project_etc_destination(pkgname):
    return os.path.join(get_global_etc_destination(), pkgname)


def get_project_include_destination(pkgname):
    return os.path.join(get_global_include_destination(), pkgname)


def get_project_lib_destination(_pkgname):
    return get_global_lib_destination()


def get_project_python_destination(pkgname):
    return os.path.join(get_global_python_destination(), pkgname)


def get_project_share_destination(pkgname):
    return os.path.join(get_global_share_destination(), pkgname)
