from __future__ import print_function

import os
import re


def get_metaproject_cmake_template_path():
    """
    Returns the location of the metaproject CMakeLists.txt CMake template.

    :returns: ``str`` location of the metaproject CMakeLists.txt CMake template
    """
    rel_path = os.path.join('templates', 'metaproject.cmake.in')
    return os.path.join(os.path.dirname(__file__), rel_path)


def configure_file(template_file, environment):
    """
    Evaluate a .in template file used in CMake with configure_file().

    :param template_file: path to the template, ``str``
    :param environment: dictionary of placeholders to substitute,
      ``dict``
    :returns: string with evaluates template
    :raises: KeyError for placeholders in the template which are not
      in the environment
    """
    with open(template_file, 'r') as f:
        template = f.read()
        return configure_string(template, environment)


def configure_string(template, environment):
    """
    Substitute variables enclosed by @ characters.

    :param template: the template, ``str``
    :param environment: dictionary of placeholders to substitute,
      ``dict``
    :returns: string with evaluates template
    :raises: KeyError for placeholders in the template which are not
      in the environment
    """
    def substitute(match):
        var = match.group(0)[1:-1]
        return environment[var]
    return re.sub('\@[a-zA-Z0-9_]+\@', substitute, template)
