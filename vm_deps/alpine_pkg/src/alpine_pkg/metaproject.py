"""
Checks metaprojects for compliance with REP-0127:
"""

from __future__ import print_function

import os

from alpine_pkg.cmake import get_metaproject_cmake_template_path
from alpine_pkg.cmake import configure_file

__author__ = "William Woodall"
__email__ = "william@osrfoundation.org"
__maintainer__ = "William Woodall"

DEFINITION_URL = 'http://ros.org/reps/rep-0127.html#metaproject'


class InvalidMetaproject(Exception):
    def __init__(self, msg, path, package):
        self.path = path
        self.package = package
        Exception.__init__(self, "Metaproject '%s': %s" % (package.name, msg))


def get_expected_cmakelists_txt(metaproject_name):
    """
    Returns the expected boilerplate CMakeLists.txt file for a metaproject

    :param metaproject_name: name of the metaproject
    :type metaproject_name: str
    :returns: expected CMakeLists.txt file
    :rtype: str
    """
    env = {
        'name': metaproject_name,
        'metaproject_arguments': ''
    }
    return configure_file(get_metaproject_cmake_template_path(), env)


def has_cmakelists_txt(path):
    """
    Returns True if the given path contains a CMakeLists.txt, otherwise False

    :param path: path to folder potentially containing CMakeLists.txt
    :type path: str
    :returns: True if path contains CMakeLists.txt, else False
    :rtype: bool
    """
    cmakelists_txt_path = os.path.join(path, 'CMakeLists.txt')
    return os.path.isfile(cmakelists_txt_path)


def get_cmakelists_txt(path):
    """
    Fetches the CMakeLists.txt from a given path

    :param path: path to the folder containing the CMakeLists.txt
    :type path: str
    :returns: contents of CMakeLists.txt file in given path
    :rtype: str
    :raises OSError: if there is no CMakeLists.txt in given path
    """
    cmakelists_txt_path = os.path.join(path, 'CMakeLists.txt')
    with open(cmakelists_txt_path, 'r') as f:
        return f.read()


def has_valid_cmakelists_txt(path, metaproject_name):
    """
    Returns True if the given path contains a valid CMakeLists.txt, otherwise False

    A valid CMakeLists.txt for a metaproject is defined by REP-0127

    :param path: path to folder containing CMakeLists.txt
    :type path: str
    :param metaproject_name: name of the metaproject being tested
    :type metaproject_name: str
    :returns: True if the path contains a valid CMakeLists.txt, else False
    :rtype: bool
    :raises OSError: if there is no CMakeLists.txt in given path
    """
    cmakelists_txt = get_cmakelists_txt(path)
    expected = get_expected_cmakelists_txt(metaproject_name)
    return cmakelists_txt == expected


def validate_metaproject(path, package):
    """
    Validates the given package (alpine_pkg.project.Project) as a metaproject

    This validates the metaproject against the definition from REP-0127

    :param path: directory of the package being checked
    :type path: str
    :param package: package to be validated
    :type package: :py:class:`alpine_pkg.project.Project`
    :raises InvalidMetaproject: if package is not a valid metaproject
    :raises OSError: if there is not project.xml at the given path
    """
    # Is there actually a package at the given path, else raise
    # Cannot do package_exists_at from alpine_pkg.projects because of circular dep
    if not os.path.isdir(path) or not os.path.isfile(os.path.join(path, 'project.xml')):
        raise OSError("No project.xml found at path: '%s'" % path)
    # Is it a metaproject, else raise
    if not package.is_metaproject():
        raise InvalidMetaproject('No <metaproject/> tag in <export> section of project.xml', path, package)
    # Is there a CMakeLists.txt, else raise
    if not has_cmakelists_txt(path):
        raise InvalidMetaproject('No CMakeLists.txt', path, package)
    # Is the CMakeLists.txt correct, else raise
    if not has_valid_cmakelists_txt(path, package.name):
        raise InvalidMetaproject("""\
Invalid CMakeLists.txt
Expected:
%s
Got:
%s""" % (get_cmakelists_txt(path), get_expected_cmakelists_txt(package.name)), path, package
        )
    # Does it buildtool depend on alpine, else raise
    if not package.has_buildtooldep_on_alpine():
        raise InvalidMetaproject("No buildtool dependency on alpine", path, package)
    # Does it have only run depends, else raise
    if package.has_invalid_metaproject_dependencies():
        raise InvalidMetaproject(
            "Has build, buildtool, and/or test depends, but only run depends are allowed (except buildtool alpine)",
            path, package)
