import em
import os
import sys
import stat
import unittest
import tempfile
import shutil

class OrderProjectsEmTest(unittest.TestCase):

    def test_env_cached_static(self):
        # hack to fix empy nosetests clash
        sys.stdout = em.ProxyFile(sys.stdout)
        template_file = os.path.join(os.path.dirname(__file__), '..', '..', 'cmake', 'em', 'order_projects.cmake.em')
        with open (template_file, 'r') as fhand:
            template = fhand.read()
        gdict = {'ALPINE_DEVEL_PREFIX': '/foo',
                 'CMAKE_PREFIX_PATH': ['/bar'],
                 'ALPINE_GLOBAL_LIB_DESTINATION': '/glob-dest/lib',
                 'ALPINE_GLOBAL_BIN_DESTINATION': '/glob-dest/bin',
                 'PYTHON_INSTALL_DIR': '/foo/dist-packages'}
        result = em.expand(template, gdict,
                           source_root_dir='/tmp/nowhere_dir',
                           whitelisted_packages=[],
                           blacklisted_packages=[])
        self.assertTrue('set(ALPINE_ORDERED_PROJECTS "")' in result, result)
        self.assertTrue('set(ALPINE_ORDERED_PROJECT_PATHS "")' in result, result)
        self.assertTrue('set(ALPINE_ORDERED_PROJECTS_IS_META "")' in result, result)
        self.assertTrue('set(ALPINE_ORDERED_PROJECTS_BUILD_TYPE "")' in result, result)
        self.assertTrue('set(ALPINE_MESSAGE_GENERATORS' in result, result)
        self.assertEqual(10, len(result.splitlines()))
