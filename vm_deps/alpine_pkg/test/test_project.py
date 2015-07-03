import unittest

# Redirect stderr to stdout to suppress output in tests
import sys
sys.stderr = sys.stdout

from alpine_pkg.project import Dependency, InvalidProject, Project, Person

from mock import Mock


class ProjectTest(unittest.TestCase):

    def get_maintainer(self):
        maint = Mock()
        maint.email = 'foo@bar.com'
        maint.name = 'John Foo'
        return maint

    def test_init(self):
        maint = self.get_maintainer()
        pack = Project(name='foo',
                       version='0.0.0',
                       maintainers=[maint],
                       licenses=['BSD'])
        self.assertEqual(None, pack.filename)
        self.assertEqual([], pack.urls)
        self.assertEqual([], pack.authors)
        self.assertEqual([maint], pack.maintainers)
        self.assertEqual(['BSD'], pack.licenses)
        self.assertEqual([], pack.builddeps)
        self.assertEqual([], pack.buildtooldeps)
        self.assertEqual([], pack.rundeps)
        self.assertEqual([], pack.testdeps)
        self.assertEqual([], pack.conflicts)
        self.assertEqual([], pack.replaces)
        self.assertEqual([], pack.exports)
        pack = Project('foo',
                       name='bar',
                       version='0.0.0',
                       licenses=['BSD'],
                       maintainers=[self.get_maintainer()])
        self.assertEqual('foo', pack.filename)

        self.assertRaises(TypeError, Project, unknownattribute=42)

    def test_init_dependency(self):
        dep = Dependency('foo',
                         lt=1,
                         lte=2,
                         eq=3,
                         gte=4,
                         gt=5)
        self.assertEquals('foo', dep.name)
        self.assertEquals(1, dep.lt)
        self.assertEquals(2, dep.lte)
        self.assertEquals(3, dep.eq)
        self.assertEquals(4, dep.gte)
        self.assertEquals(5, dep.gt)
        self.assertRaises(TypeError, Dependency, 'foo', unknownattribute=42)

    def test_init_kwargs_string(self):
        pack = Project('foo',
                       name='bar',
                       format='1',
                       version='0.0.0',
                       abi='pabi',
                       description='pdesc',
                       licenses=['BSD'],
                       maintainers=[self.get_maintainer()])
        self.assertEqual('foo', pack.filename)
        self.assertEqual('bar', pack.name)
        self.assertEqual('1', pack.format)
        self.assertEqual('pabi', pack.abi)
        self.assertEqual('0.0.0', pack.version)
        self.assertEqual('pdesc', pack.description)

    def test_init_kwargs_object(self):
        mmain = [self.get_maintainer(), self.get_maintainer()]
        mlis = ['MIT', 'BSD']
        mauth = [self.get_maintainer(), self.get_maintainer()]
        murl = [Mock(), Mock()]
        mbuilddep = [Mock(), Mock()]
        mbuildtooldep = [Mock(), Mock()]
        mrundep = [Mock(), Mock()]
        mtestdep = [Mock(), Mock()]
        mconf = [Mock(), Mock()]
        mrepl = [Mock(), Mock()]
        mexp = [Mock(), Mock()]
        pack = Project(name='bar',
                       version='0.0.0',
                       maintainers=mmain,
                       licenses=mlis,
                       urls=murl,
                       authors=mauth,
                       builddeps=mbuilddep,
                       buildtooldeps=mbuildtooldep,
                       rundeps=mrundep,
                       testdeps=mtestdep,
                       conflicts=mconf,
                       replaces=mrepl,
                       exports=mexp)
        self.assertEqual(mmain, pack.maintainers)
        self.assertEqual(mlis, pack.licenses)
        self.assertEqual(murl, pack.urls)
        self.assertEqual(mauth, pack.authors)
        self.assertEqual(mbuilddep, pack.builddeps)
        self.assertEqual(mbuildtooldep, pack.buildtooldeps)
        self.assertEqual(mrundep, pack.rundeps)
        self.assertEqual(mtestdep, pack.testdeps)
        self.assertEqual(mconf, pack.conflicts)
        self.assertEqual(mrepl, pack.replaces)
        self.assertEqual(mexp, pack.exports)

    def test_validate_project(self):
        maint = self.get_maintainer()
        pack = Project('foo',
                       name='bar_2go',
                       format='1',
                       version='0.0.0',
                       abi='pabi',
                       description='pdesc',
                       licenses=['BSD'],
                       maintainers=[maint])
        pack.validate()
        # check invalid names
        pack.name = '2bar'
        pack.validate()
        pack.name = 'bar bza'
        self.assertRaises(InvalidProject, Project.validate, pack)
        pack.name = 'bar-bza'
        # valid for now because for backward compatibility only
        #self.assertRaises(InvalidProject, Project.validate, pack)
        pack.name = 'BAR'
        pack.validate()
        # check authors emails
        pack.name = 'bar'
        auth1 = Mock()
        auth2 = Mock()
        auth2.validate.side_effect = InvalidProject('foo')
        pack.authors = [auth1, auth2]
        self.assertRaises(InvalidProject, Project.validate, pack)
        pack.authors = []
        pack.validate()
        # check maintainer required with email
        pack.maintainers = []
        self.assertRaises(InvalidProject, Project.validate, pack)
        pack.maintainers = [maint]
        maint.email = None
        self.assertRaises(InvalidProject, Project.validate, pack)
        maint.email = 'foo@bar.com'

        for dep_type in [pack.builddeps, pack.buildtooldeps, pack.rundeps, pack.testdeps]:
            pack.validate()
            depend = Dependency(pack.name)
            dep_type.append(depend)
            self.assertRaises(InvalidProject, Project.validate, pack)
            dep_type.remove(depend)

    def test_validate_person(self):
        auth1 = Person('foo')
        auth1.email = 'foo@bar.com'
        auth1.validate()
        auth1.email = 'foo-bar@bar.com'
        auth1.validate()
        auth1.email = 'foo+bar@bar.com'
        auth1.validate()

        auth1.email = 'foo[at]bar.com'
        self.assertRaises(InvalidProject, Person.validate, auth1)
        auth1.email = 'foo bar.com'
        self.assertRaises(InvalidProject, Person.validate, auth1)
        auth1.email = 'foo<bar.com'
        self.assertRaises(InvalidProject, Person.validate, auth1)
