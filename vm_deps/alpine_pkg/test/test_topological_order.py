from __future__ import print_function
import unittest
from mock import Mock
try:
    from alpine_pkg.topological_order import topological_order_projects, _ProjectDecorator, \
        _sort_decorated_projects
except ImportError as e:
    raise ImportError('Please adjust your PYTHONPATH before running this test: %s' % str(e))


class TopologicalOrderTest(unittest.TestCase):

    def test_topological_order_projects(self):
        def create_mock(name, builddeps, rundeps, path):
            m = Mock()
            m.name = name
            m.builddeps = builddeps
            m.buildtooldeps = []
            m.rundeps = rundeps
            m.exports = []
            m.path = path
            return m

        mc = create_mock('c', [], [], 'pc')
        md = create_mock('d', [], [], 'pd')
        ma = create_mock('a', [mc], [md], 'pa')
        mb = create_mock('b', [ma], [], 'pb')

        projects = {ma.path: ma,
                    mb.path: mb,
                    mc.path: mc,
                    md.path: md}

        ordered_projects = topological_order_projects(projects, blacklisted=['c'])
        # d before b because of the run dependency from a to d
        # a before d only because of alphabetic order, a run depend on d should not influence the order
        self.assertEqual(['pa', 'pd', 'pb'], [path for path, _ in ordered_projects])

        ordered_projects = topological_order_projects(projects, whitelisted=['a', 'b', 'c'])
        # c before a because of the run dependency from a to c
        self.assertEqual(['pc', 'pa', 'pb'], [path for path, _ in ordered_projects])

    def test_project_decorator_init(self):

        mockproject = Mock()

        mockexport = Mock()
        mockexport.tagname = 'message_generator'
        mockexport.content = 'foolang'
        mockproject.exports = [mockexport]

        pd = _ProjectDecorator(mockproject, 'foo/bar')
        self.assertEqual(mockproject.name, pd.name)
        self.assertEqual('foo/bar', pd.path)
        self.assertFalse(pd.is_metaproject)
        self.assertEqual(mockexport.content, pd.message_generator)
        self.assertIsNotNone(str(pd))

    def test_calculate_depends_for_topological_order(self):
        def create_mock(name, rundeps):
            m = Mock()
            m.name = name
            m.builddeps = []
            m.buildtooldeps = []
            m.rundeps = rundeps
            m.exports = []
            return m

        mockproject1 = _ProjectDecorator(create_mock('n1', []), 'p1')
        mockproject2 = _ProjectDecorator(create_mock('n2', []), 'p2')
        mockproject3 = _ProjectDecorator(create_mock('n3', []), 'p3')
        mockproject4 = _ProjectDecorator(create_mock('n4', []), 'p4')
        mockproject5 = _ProjectDecorator(create_mock('n5', [mockproject4]), 'p5')
        mockproject6 = _ProjectDecorator(create_mock('n6', [mockproject5]), 'p6')
        mockproject7 = _ProjectDecorator(create_mock('n7', []), 'p7')

        mockproject = Mock()
        mockproject.builddeps = [mockproject1, mockproject2]
        mockproject.buildtooldeps = [mockproject3, mockproject6]
        mockproject.rundeps = [mockproject7]
        mockproject.exports = []

        pd = _ProjectDecorator(mockproject, 'foo/bar')
        # 2 and 3 as external dependencies
        projects = {mockproject1.name: mockproject1,
                    mockproject4.name: mockproject4,
                    mockproject5.name: mockproject5,
                    mockproject6.name: mockproject6}

        pd.calculate_depends_for_topological_order(projects)
        self.assertEqual(set([mockproject1.name, mockproject4.name, mockproject5.name, mockproject6.name]), pd.depends_for_topological_order)

    def test_sort_decorated_projects(self):
        projects = {}
        sprojects = _sort_decorated_projects(projects)
        self.assertEqual([], sprojects)

        def create_mock(path):
            m = Mock()
            m.path = path
            m.depends_for_topological_order = set()
            m.message_generator = False
            return m

        mock1 = create_mock('mock1')
        mock2 = create_mock('mock2')
        mock3 = create_mock('mock3')
        mock3.message_generator = True

        projects = {'mock3': mock3, 'mock2': mock2, 'mock1': mock1}
        sprojects = _sort_decorated_projects(projects)

        # mock3 first since it is a message generator
        # mock1 before mock2 due to alphabetic order 
        self.assertEqual(['mock3', 'mock1', 'mock2'], [path for path, _ in sprojects])

    def test_sort_decorated_projects_favoring_message_generators(self):
        def create_mock(path):
            m = Mock()
            m.path = path
            m.depends_for_topological_order = set()
            m.message_generator = False
            return m

        mock1 = create_mock('mock1')
        mock2 = create_mock('mock2')
        mock3 = create_mock('mock3')
        mock3.depends_for_topological_order = set(['mock2'])
        mock3.message_generator = True

        projects = {'mock3': mock3, 'mock2': mock2, 'mock1': mock1}
        sprojects = _sort_decorated_projects(projects)

        # mock2 first since it is the dependency of a message generator
        # mock3 since it is a message generator
        # mock1 last, although having no dependencies and being first in alphabetic order 
        self.assertEqual(['mock2', 'mock3', 'mock1'], [path for path, _ in sprojects])

    def test_sort_decorated_projects_cycles(self):
        def create_mock(path, depend):
            m = Mock()
            m.path = path
            m.depends_for_topological_order = set([depend])
            m.message_generator = False
            return m

        # creating a cycle for cycle detection
        mock1 = create_mock('mock1', 'mock2')
        mock2 = create_mock('mock2', 'mock3')
        mock3 = create_mock('mock3', 'mock4')
        mock4 = create_mock('mock4', 'mock2')

        projects = {'mock3': mock3, 'mock2': mock2, 'mock1': mock1, 'mock4': mock4}
        sprojects = _sort_decorated_projects(projects)
        self.assertEqual([[None, 'mock2, mock3, mock4']], sprojects)

        # remove cycle
        mock4.depends_for_topological_order = set()
        sprojects = _sort_decorated_projects(projects)

        # mock4 first since it has no dependencies
        # than mock3 since it only had mock4 as a dependency
        # than mock2 since it only had mock3 as a dependency
        # than mock1 since it only had mock2 as a dependency
        self.assertEqual(['mock4', 'mock3', 'mock2', 'mock1'], [path for path, _ in sprojects])

    def test_topological_order_projects_with_underlay(self):
        def create_mock(name, builddeps, path):
            m = Mock()
            m.name = name
            m.builddeps = builddeps
            m.buildtooldeps = []
            m.rundeps = []
            m.exports = []
            m.path = path
            return m

        mc = create_mock('c', [], 'pc')
        mb = create_mock('b', [mc], 'pb')
        ma = create_mock('a', [mb], 'pa')

        projects = {ma.path: ma,
                    mc.path: mc}
        underlay_projects = {mb.path: mb}
        ordered_projects = topological_order_projects(projects, underlay_projects=underlay_projects)
        # c before a because of the indirect dependency via b which is part of an underlay
        self.assertEqual(['pc', 'pa'], [path for path, _ in ordered_projects])

