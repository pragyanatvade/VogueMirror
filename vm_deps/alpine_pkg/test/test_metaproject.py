from __future__ import print_function

import contextlib
import os
import re
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import sys
import unittest

from alpine_pkg.metaproject import get_expected_cmakelists_txt
from alpine_pkg.metaproject import InvalidMetaproject
from alpine_pkg.metaproject import validate_metaproject

from alpine_pkg.projects import find_projects

test_data_dir = os.path.join(os.path.dirname(__file__), 'data', 'metaprojects')

test_expectations = {
    # Test name: [ExceptionType or None, ExceptionRegex or None, WarningRegex or None]
    'invalid_cmake': [InvalidMetaproject, 'Invalid CMakeLists.txt', None],
    'invalid_depends': [InvalidMetaproject, 'Has build, buildtool, and/or test depends', None],
    'leftover_files': [None, None, None],
    'no_buildtooldep_alpine': [InvalidMetaproject, 'No buildtool dependency on alpine', None],
    'no_cmake': [InvalidMetaproject, 'No CMakeLists.txt', None],
    'no_metaproject_tag': [InvalidMetaproject, 'No <metaproject/> tag in <export>', None],
    'valid_metaproject': [None, None, None]
}


@contextlib.contextmanager
def assert_warning(warnreg):
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    try:
        out = StringIO()
        sys.stdout = out
        sys.stderr = sys.stdout
        yield
    finally:
        if warnreg is not None:
            out = out.getvalue()
            assert re.search(warnreg, out) is not None, "'%s' does not match warning '%s'" % (warnreg, out)
        else:
            print(out)
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


def _validate_metaproject(path, project):
    try:
        validate_metaproject(path, project)
    except Exception:
        # print('on project ' + project.name, file=sys.stderr)
        raise


class TestMetaprojectValidation(unittest.TestCase):
    """Tests the metaproject validator"""
    def test_validate_metaproject(self):
        pkgs_dict = find_projects(test_data_dir)
        for path, project in pkgs_dict.items():
            path = os.path.join(test_data_dir, path)
            assert project.name in test_expectations, 'Unknown test %s' % project.name
            exc, excreg, warnreg = test_expectations[project.name]
            with assert_warning(warnreg):
                if exc is not None:
                    if excreg is not None:
                        with self.assertRaisesRegexp(exc, excreg):
                            _validate_metaproject(path, project)
                    else:
                        with self.assertRaises(exc):
                            _validate_metaproject(path, project)
                else:
                    _validate_metaproject(path, project)


def test_get_expected_cmakelists_txt():
    expected = '''\
cmake_minimum_required(VERSION 2.8.3)
project(example)
find_package(alpine REQUIRED)
alpine_metaproject()
'''
    assert expected == get_expected_cmakelists_txt('example')
