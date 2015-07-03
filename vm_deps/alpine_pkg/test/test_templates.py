import os
import unittest
import tempfile
import shutil

from mock import MagicMock, Mock

from alpine_pkg.project_templates import _safe_write_files, create_project_files, \
    create_cmakelists, create_project_xml, ProjectTemplate, _create_include_macro, \
    _create_targetlib_args
from alpine_pkg.project import parse_project, Dependency, Export, Url, PROJECT_MANIFEST_FILENAME
from alpine_pkg.python_setup import generate_distutils_setup


class TemplateTest(unittest.TestCase):

    def get_maintainer(self):
        maint = Mock()
        maint.email = 'foo@bar.com'
        maint.name = 'John Foo'
        return maint

    def test_safe_write_files(self):
        file1 = os.path.join('foo', 'bar')
        file2 = os.path.join('foo', 'baz')
        newfiles = {file1: 'foobar', file2: 'barfoo'}
        try:
            rootdir = tempfile.mkdtemp()
            _safe_write_files(newfiles, rootdir)
            self.assertTrue(os.path.isfile(os.path.join(rootdir, file1)))
            self.assertTrue(os.path.isfile(os.path.join(rootdir, file2)))
            self.assertRaises(ValueError, _safe_write_files, newfiles, rootdir)
        finally:
            shutil.rmtree(rootdir)

    def test_create_cmakelists(self):
        mock_pack = MagicMock()
        mock_pack.name = 'foo'
        mock_pack.alpine_deps = []
        result = create_cmakelists(mock_pack, 'groovy')
        self.assertTrue('project(foo)' in result, result)
        self.assertTrue('find_package(alpine REQUIRED)' in result, result)

        mock_pack.alpine_deps = ['bar', 'baz']
        result = create_cmakelists(mock_pack, 'groovy')
        self.assertTrue('project(foo)' in result, result)
        expected = """find_package(alpine REQUIRED COMPONENTS
  bar
  baz
)"""
        
        self.assertTrue(expected in result, result)

    def test_create_project_xml(self):
        maint = self.get_maintainer()
        pack = ProjectTemplate(name='foo',
                               description='foo',
                               version='0.0.0',
                               maintainers=[maint],
                               licenses=['BSD'])

        result = create_project_xml(pack, 'groovy')
        self.assertTrue('<name>foo</name>' in result, result)

    def test_create_targetlib_args(self):
        mock_pack = MagicMock()
        mock_pack.name = 'foo'
        mock_pack.alpine_deps = []
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${alpine_LIBRARIES}\n', statement)
        mock_pack.alpine_deps = ['cpp', 'py']
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${alpine_LIBRARIES}\n', statement)
        mock_pack.alpine_deps = ['cpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = []
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${alpine_LIBRARIES}\n#   ${Boost_LIBRARIES}\n', statement)
        mock_pack.alpine_deps = ['cpp']
        mock_pack.boost_comps = []
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${alpine_LIBRARIES}\n#   ${log4cxx_LIBRARIES}\n#   ${BZip2_LIBRARIES}\n', statement)
        mock_pack.alpine_deps = ['cpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_targetlib_args(mock_pack)
        self.assertEqual('#   ${alpine_LIBRARIES}\n#   ${Boost_LIBRARIES}\n#   ${log4cxx_LIBRARIES}\n#   ${BZip2_LIBRARIES}\n', statement)

    def test_create_include_macro(self):
        mock_pack = MagicMock()
        mock_pack.name = 'foo'
        mock_pack.alpine_deps = []
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include_directories(include)', statement)
        mock_pack.alpine_deps = ['cpp', 'py']
        mock_pack.boost_comps = []
        mock_pack.system_deps = []
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include_directories(include)\ninclude_directories(\n  ${alpine_INCLUDE_DIRS}\n)', statement)
        mock_pack.alpine_deps = ['cpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = []
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include_directories(include)\ninclude_directories(\n  ${alpine_INCLUDE_DIRS}\n  ${Boost_INCLUDE_DIRS}\n)', statement)
        mock_pack.alpine_deps = ['cpp']
        mock_pack.boost_comps = []
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include_directories(include)\n# TODO: Check names of system library include directories (log4cxx, BZip2)\ninclude_directories(\n  ${alpine_INCLUDE_DIRS}\n  ${log4cxx_INCLUDE_DIRS}\n  ${BZip2_INCLUDE_DIRS}\n)', statement)
        mock_pack.alpine_deps = ['cpp']
        mock_pack.boost_comps = ['thread', 'filesystem']
        mock_pack.system_deps = ['log4cxx', 'BZip2']
        statement = _create_include_macro(mock_pack)
        self.assertEqual('# include_directories(include)\n# TODO: Check names of system library include directories (log4cxx, BZip2)\ninclude_directories(\n  ${alpine_INCLUDE_DIRS}\n  ${Boost_INCLUDE_DIRS}\n  ${log4cxx_INCLUDE_DIRS}\n  ${BZip2_INCLUDE_DIRS}\n)', statement)

    def test_create_project(self):
        maint = self.get_maintainer()
        pack = ProjectTemplate(name='bar',
                               description='bar',
                               format='1',
                               version='0.0.0',
                               abi='pabi',
                               maintainers=[maint],
                               licenses=['BSD'])
        try:
            rootdir = tempfile.mkdtemp()
            file1 = os.path.join(rootdir, 'CMakeLists.txt')
            file2 = os.path.join(rootdir, PROJECT_MANIFEST_FILENAME)
            create_project_files(rootdir, pack, 'alpine', {file1: ''})
            self.assertTrue(os.path.isfile(file1))
            self.assertTrue(os.path.isfile(file2))
        finally:
            shutil.rmtree(rootdir)


    def test_create_project_template(self):
        template = ProjectTemplate._create_project_template(
            project_name='bar2',
            alpine_deps=['dep1', 'dep2'])
        self.assertEqual('dep1', template.builddeps[0].name)
        self.assertEqual('dep2', template.builddeps[1].name)

    def test_parse_generated(self):
        maint = self.get_maintainer()
        pack = ProjectTemplate(name='bar',
                               format=1,
                               version='0.0.0',
                               abi='pabi',
                               urls=[Url('foo')],
                               description='pdesc',
                               maintainers=[maint],
                               licenses=['BSD'])
        try:
            rootdir = tempfile.mkdtemp()
            file1 = os.path.join(rootdir, 'CMakeLists.txt')
            file2 = os.path.join(rootdir, PROJECT_MANIFEST_FILENAME)
            create_project_files(rootdir, pack, 'groovy')
            self.assertTrue(os.path.isfile(file1))
            self.assertTrue(os.path.isfile(file2))

            pack_result = parse_project(file2)
            self.assertEqual(pack.name, pack_result.name)
            self.assertEqual(pack.format, pack_result.format)
            self.assertEqual(pack.version, pack_result.version)
            self.assertEqual(pack.abi, pack_result.abi)
            self.assertEqual(pack.description, pack_result.description)
            self.assertEqual(pack.maintainers[0].name, pack_result.maintainers[0].name)
            self.assertEqual(pack.maintainers[0].email, pack_result.maintainers[0].email)
            self.assertEqual(pack.authors, pack_result.authors)
            self.assertEqual(pack.urls[0].url, pack_result.urls[0].url)
            self.assertEqual('website', pack_result.urls[0].type)
            self.assertEqual(pack.licenses, pack_result.licenses)
            self.assertEqual(pack.builddeps, pack_result.builddeps)
            self.assertEqual(pack.buildtooldeps, pack_result.buildtooldeps)
            self.assertEqual(pack.rundeps, pack_result.rundeps)
            self.assertEqual(pack.testdeps, pack_result.testdeps)
            self.assertEqual(pack.conflicts, pack_result.conflicts)
            self.assertEqual(pack.replaces, pack_result.replaces)
            self.assertEqual(pack.exports, pack_result.exports)

            rdict = generate_distutils_setup(project_xml_path=file2)
            self.assertEqual({'name': 'bar',
                              'maintainer': u'John Foo',
                              'maintainer_email': 'foo@bar.com',
                              'description': 'pdesc',
                              'license': 'BSD',
                              'version': '0.0.0',
                              'author': '',
                              'url': 'foo'}, rdict)
        finally:
            shutil.rmtree(rootdir)

    def test_parse_generated_multi(self):
        # test with multiple attributes filled
        maint = self.get_maintainer()
        pack = ProjectTemplate(name='bar',
                               format=1,
                               version='0.0.0',
                               abi='pabi',
                               description='pdesc',
                               maintainers=[maint, maint],
                               authors=[maint, maint],
                               licenses=['BSD', 'MIT'],
                               urls=[Url('foo', 'bugtracker'), Url('bar')],
                               builddeps=[Dependency('dep1')],
                               buildtooldeps=[Dependency('dep2'),
                                                      Dependency('dep3')],
                               rundeps=[Dependency('dep4')],
                               testdeps=[Dependency('dep5')],
                               conflicts=[Dependency('dep6')],
                               replaces=[Dependency('dep7'),
                                             Dependency('dep8')],
                               exports=[Export('architecture_independent'),
                                        Export('meta_project')])

        def assertEqualDependencies(deplist1, deplist2):
            if len(deplist1) != len(deplist1):
                return False
            for depx, depy in zip(deplist1, deplist2):
                for attr in ['name', 'lt', 'lte',
                             'eq', 'gte', 'gt']:
                    if getattr(depx, attr) != getattr(depy, attr):
                        return False
            return True

        try:
            rootdir = tempfile.mkdtemp()
            file1 = os.path.join(rootdir, 'CMakeLists.txt')
            file2 = os.path.join(rootdir, PROJECT_MANIFEST_FILENAME)
            create_project_files(rootdir, pack, 'alpine')
            self.assertTrue(os.path.isfile(file1))
            self.assertTrue(os.path.isfile(file2))

            pack_result = parse_project(file2)
            self.assertEqual(pack.name, pack_result.name)
            self.assertEqual(pack.format, pack_result.format)
            self.assertEqual(pack.version, pack_result.version)
            self.assertEqual(pack.abi, pack_result.abi)
            self.assertEqual(pack.description, pack_result.description)
            self.assertEqual(len(pack.maintainers), len(pack_result.maintainers))
            self.assertEqual(len(pack.authors), len(pack_result.authors))
            self.assertEqual(len(pack.urls), len(pack_result.urls))
            self.assertEqual(pack.urls[0].url, pack_result.urls[0].url)
            self.assertEqual(pack.urls[0].type, pack_result.urls[0].type)
            self.assertEqual(pack.licenses, pack_result.licenses)
            self.assertTrue(assertEqualDependencies(pack.builddeps,
                                                    pack_result.builddeps))
            self.assertTrue(assertEqualDependencies(pack.builddeps,
                                                    pack_result.builddeps))
            self.assertTrue(assertEqualDependencies(pack.buildtooldeps,
                                                    pack_result.buildtooldeps))
            self.assertTrue(assertEqualDependencies(pack.rundeps,
                                                    pack_result.rundeps))
            self.assertTrue(assertEqualDependencies(pack.testdeps,
                                                    pack_result.testdeps))
            self.assertTrue(assertEqualDependencies(pack.conflicts,
                                                    pack_result.conflicts))
            self.assertTrue(assertEqualDependencies(pack.replaces,
                                                    pack_result.replaces))
            self.assertEqual(pack.exports[0].tagname, pack_result.exports[0].tagname)
            self.assertEqual(pack.exports[1].tagname, pack_result.exports[1].tagname)

            rdict = generate_distutils_setup(project_xml_path=file2)
            self.assertEqual({'name': 'bar',
                              'maintainer': u'John Foo <foo@bar.com>, John Foo <foo@bar.com>',
                              'description': 'pdesc',
                              'license': 'BSD, MIT',
                              'version': '0.0.0',
                              'author': u'John Foo <foo@bar.com>, John Foo <foo@bar.com>',
                              'url': 'bar'}, rdict)
        finally:
            shutil.rmtree(rootdir)
