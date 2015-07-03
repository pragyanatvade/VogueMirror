#!/usr/bin/env python

import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from test.utils import AbstractAlpineWorkspaceTest, MOCK_DIR, \
    MAKE_CMD, succeed, assert_exists, fail


import em
import sys
import stat
import unittest
import tempfile




class MockTest(AbstractAlpineWorkspaceTest):
    """
    This test case uses workspaces with alpine projects from the
    test/mock_resources folder.
    """

    # uncomment to keep temporary files in /tmp
    # def tearDown(self):
    #     pass

    def test_alpine_only(self):
        self.cmake()
        succeed(MAKE_CMD, cwd=self.builddir)
        succeed(MAKE_CMD + ["install"], cwd=self.builddir)

        assert_exists(self.installdir,
                      "env.sh",
                      "setup.sh",
                      "setup.zsh")

    def test_nolang(self):
        dstdir = os.path.join(self.workspacedir, 'nolangs')
        shutil.copytree(os.path.join(MOCK_DIR, 'src', 'nolangs'), dstdir)

        out = self.cmake(ALPINE_WHITELIST_PROJECTS='nolangs',
                         ALPINE_DPKG_BUILDPROJECT_FLAGS='-d;-S;-us;-uc')
        self.assertTrue(os.path.exists(self.builddir + "/nolangs"))
        self.assertFalse(os.path.exists(self.builddir + "/std_msgs"))
        self.assertFalse(os.path.exists(self.builddir + "/genmsg"))
        out = succeed(MAKE_CMD, cwd=self.builddir)
        self.assertTrue(os.path.exists(self.builddir +
                                       "/nolangs/bin/nolangs_exec"))
        out = succeed(MAKE_CMD + ["install"], cwd=self.builddir)

        assert_exists(self.installdir,
                      "bin/nolangs_exec",
                      "share/nolangs/cmake/nolangsConfig.cmake")

        # also test make help
        succeed(MAKE_CMD + ["help"], cwd=self.builddir)

    def test_noproject(self):
        # create workspace with just alpine and 'noproject' project
        dstdir = os.path.join(self.workspacedir, 'noproject')
        shutil.copytree(os.path.join(MOCK_DIR, 'src-fail', 'noproject'), dstdir)
        # test with whitelist
        out = self.cmake(ALPINE_WHITELIST_PROJECTS='alpine')
        out = succeed(MAKE_CMD + ["install"], cwd=self.builddir)

        shutil.rmtree(self.builddir)
        # fail if we try to build noproject stack
        os.makedirs(self.builddir)

        out = self.cmake(CMAKE_PREFIX_PATH=self.installdir,
                         expect=fail)
        print("failed as expected, out=", out)

        self.assertTrue("alpine_project() PROJECT_NAME is set to 'Project'" in out, out)
        # assert 'You must call project() with the same name before.' in out

    # Test was not finished apparently
    # def test_help_bad_changelog(self):
    #     self.cmake(ALPINE_ENABLE_DEBBUILDING='TRUE',
    #           CMAKE_PREFIX_PATH=diskprefix,
    #           srcdir=os.path.join(MOCK_DIR,
    #                               'src-fail', 'badly_specified_changelog'),
    #           ALPINE='YES')
    #     succeed(MAKE_CMD + ['help'], cwd=self.builddir)

    def test_env_cached_static(self):
        # hack to fix empy nosetests clash
        sys.stdout = em.ProxyFile(sys.stdout)
        dstdir = os.path.join(self.workspacedir, 'alpine_test')
        shutil.copytree(os.path.join(MOCK_DIR, 'src', 'alpine_test'), dstdir)
        template_file = os.path.join(os.path.dirname(__file__), '..', '..', 'cmake', 'em', 'order_projects.cmake.em')
        with open (template_file, 'r') as fhand:
            template = fhand.read()
        gdict = {'ALPINE_DEVEL_PREFIX': '/foo',
                 'CMAKE_PREFIX_PATH': ['/bar'],
                 'ALPINE_GLOBAL_LIB_DESTINATION': '/glob-dest/lib',
                 'ALPINE_GLOBAL_BIN_DESTINATION': '/glob-dest/bin',
                 'PYTHON_INSTALL_DIR': '/foo/dist-packages'}
        result = em.expand(template, gdict,
                           source_root_dir=self.workspacedir,
                           whitelisted_packages=None,
                           blacklisted_packages=None)
        self.assertTrue('set(ALPINE_ORDERED_PROJECTS "")' in result, result)
        self.assertTrue('set(ALPINE_ORDERED_PROJECT_PATHS "")' in result, result)
        self.assertTrue('set(ALPINE_ORDERED_PROJECTS_IS_META "")' in result, result)
        self.assertTrue('set(ALPINE_MESSAGE_GENERATORS' in result, result)

#         self.assertTrue("""\
# list(APPEND ALPINE_ORDERED_PROJECTS "alpine_test")
# list(APPEND ALPINE_ORDERED_PROJECT_PATHS "alpine_test/alpine_test")
# list(APPEND ALPINE_ORDERED_PROJECTS_IS_META "True")
# list(APPEND ALPINE_ORDERED_PROJECTS_BUILD_TYPE "alpine")""" in result, result)
#         self.assertTrue("""\
# list(APPEND ALPINE_ORDERED_PROJECTS "a")
# list(APPEND ALPINE_ORDERED_PROJECT_PATHS "alpine_test/a")
# list(APPEND ALPINE_ORDERED_PROJECTS_IS_META "False")
# list(APPEND ALPINE_ORDERED_PROJECTS_BUILD_TYPE "alpine")""" in result, result)
#         # alpine itself filtered out
        self.assertFalse('list(APPEND ALPINE_ORDERED_PROJECTS "alpine"' in result, result)
        self.assertEqual(10, len(result.splitlines()))
