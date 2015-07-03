import os
import sys
import unittest
import tempfile
import shutil

import mock

try:
    import alpine_pkg
    from alpine_pkg.project_templates import ProjectTemplate
except ImportError as impe:
    raise ImportError(
        'Please adjust your pythonpath before running this test: %s' % str(impe))

import imp
imp.load_source('alpine_create_project',
                os.path.join(os.path.dirname(__file__),
                             '..', 'bin', 'alpine_create_project'))

from alpine_create_project import main


class CreateProjectTest(unittest.TestCase):

    def test_create_project_template(self):
        template = ProjectTemplate._create_project_template('fooproject')
        self.assertEqual('fooproject', template.name)
        self.assertEqual('0.0.0', template.version)
        self.assertEqual('The fooproject project', template.description)
        self.assertEqual([], template.alpine_deps)
        self.assertEqual([], template.authors)
        self.assertEqual(1, len(template.maintainers))
        self.assertIsNotNone(template.maintainers[0].email)
        self.assertEqual([], template.urls)
        # with args
        template = ProjectTemplate._create_project_template(
            'fooproject',
            description='foo_desc',
            licenses=['a', 'b'],
            maintainer_names=['John Doe', 'Rishabh'],
            author_names=['Pragyan'],
            version='1.2.3',
            alpine_deps=['foobar', 'baz'])
        self.assertEqual('fooproject', template.name)
        self.assertEqual('1.2.3', template.version)
        self.assertEqual('foo_desc', template.description)
        self.assertEqual(['baz', 'foobar'], template.alpine_deps)
        self.assertEqual(1, len(template.authors))
        self.assertEqual('John Doe', template.maintainers[0].name)
        self.assertEqual('Rishabh', template.maintainers[1].name)
        self.assertEqual('Pragyan', template.authors[0].name)
        self.assertEqual(2, len(template.maintainers))
        self.assertEqual([], template.urls)

    def test_main(self):
        try:
            root_dir = tempfile.mkdtemp()
            main(['--distro', 'alpine', 'foo'], root_dir)
            self.assertTrue(os.path.isdir(os.path.join(root_dir, 'foo')))
            self.assertTrue(os.path.isfile(os.path.join(root_dir, 'foo', 'CMakeLists.txt')))
            self.assertTrue(os.path.isfile(os.path.join(root_dir, 'foo', 'project.xml')))
        finally:
            shutil.rmtree(root_dir)
