import os
import unittest
import tempfile
import shutil

from mock import Mock

try:
    import alpine
    from alpine.find_in_workspaces import find_in_workspaces, _get_valid_search_dirs
    from alpine.workspace import ALPINE_MARKER_FILE
except ImportError as impe:
    raise ImportError(
        'Please adjust your pythonpath before running this test: %s' % str(impe))


class FindInWorkspaceTest(unittest.TestCase):

    def test_get_valid_search_dirs(self):
        self.assertEqual(['bin', 'etc', 'include', 'lib', 'share'], _get_valid_search_dirs([], None))
        self.assertEqual(['bin', 'etc', 'include', 'lib', 'share'], _get_valid_search_dirs(None, None))
        self.assertEqual(['etc', 'include', 'libexec', 'share'],
                         _get_valid_search_dirs(None, 'foo'))
        self.assertEqual(['bin', 'etc', 'include', 'lib', 'share'],
                         _get_valid_search_dirs(None, None))
        self.assertEqual(['include', 'bin'],
                         _get_valid_search_dirs(['include', 'bin'], None))
        self.assertEqual(['include', 'etc'],
                         _get_valid_search_dirs(['include', 'etc'], 'foo'))

        self.assertRaises(ValueError, _get_valid_search_dirs, ['foo'], None)
        self.assertRaises(ValueError, _get_valid_search_dirs, ['bin'], 'foo')
        self.assertRaises(ValueError, _get_valid_search_dirs, ['libexec'], None)

    def test_find_in_workspaces(self):
        existing = find_in_workspaces([], _workspaces=None)
        self.assertEqual([], existing)
        existing = find_in_workspaces([], 'foo', _workspaces=None)
        self.assertEqual([], existing)
        existing = find_in_workspaces([], 'foo', 'foopath', _workspaces=None)
        self.assertEqual([], existing)

        existing = find_in_workspaces(['include'], 'foo', 'foopath', _workspaces=None)
        self.assertEqual([], existing)

        checked = []
        existing = find_in_workspaces(['include'], 'foo', 'foopath', _workspaces=['bar'], considered_paths=checked)
        self.assertEqual([], existing)
        self.assertEqual(['bar/include/foo/foopath'], checked)
        checked = []
        existing = find_in_workspaces(['include'], 'foo', 'foopath', _workspaces=['bar', 'baz'], considered_paths=checked)
        self.assertEqual([], existing)
        self.assertEqual(['bar/include/foo/foopath', 'baz/include/foo/foopath'], checked)
        checked = []
        existing = find_in_workspaces(['include', 'etc', 'libexec'], 'foo', 'foopath', _workspaces=['bar', 'baz'], considered_paths=checked)
        self.assertEqual([], existing)
        self.assertEqual(['bar/include/foo/foopath',
                          'bar/etc/foo/foopath',
                          'bar/lib/foo/foopath',
                          'baz/include/foo/foopath',
                          'baz/etc/foo/foopath',
                          'baz/lib/foo/foopath'], checked)
        checked = []
        existing = find_in_workspaces(['share', 'etc', 'lib'], None, 'foopath', _workspaces=['bar', 'baz'], considered_paths=checked)
        self.assertEqual([], existing)
        self.assertEqual(['bar/share/foopath',
                          'bar/etc/foopath',
                          'bar/lib/foopath',
                          'baz/share/foopath',
                          'baz/etc/foopath',
                          'baz/lib/foopath'], checked)
        checked = []
        existing = find_in_workspaces(None, None, None, _workspaces=['bar'], considered_paths=checked)
        self.assertEqual([], existing)
        self.assertEqual(['bar/bin', 'bar/etc', 'bar/include', 'bar/lib', 'bar/share'], checked)

    def test_with_sourcepath(self):
        def create_mock_workspace(root_dir, ws):
            ws1 = os.path.join(root_dir, ws)
            inc = os.path.join(ws1, "include")
            share = os.path.join(ws1, "share")
            p1inc = os.path.join(inc, "foo")
            p1share = os.path.join(share, "foo")
            os.makedirs(ws1)
            os.makedirs(inc)
            os.makedirs(share)
            os.makedirs(p1inc)
            os.makedirs(p1share)
            with open(os.path.join(ws1, ALPINE_MARKER_FILE), 'w') as fhand:
                fhand.write('loc1;loc2')

        try:
            fp_backup = alpine.find_in_workspaces.find_projects
            root_dir = tempfile.mkdtemp()
            alpine.find_in_workspaces.find_projects = Mock()
            foomock = Mock()
            foomock.name = 'foo'
            barmock = Mock()
            barmock.name = 'bar'
            alpine.find_in_workspaces.find_projects.return_value = {'bar': barmock, 'foo': foomock}
            create_mock_workspace(root_dir, 'ws1')
            create_mock_workspace(root_dir, 'ws2')
            checked = []
            existing = find_in_workspaces(['share', 'etc'], 'foo', 'foopath', _workspaces=[os.path.join(root_dir, 'ws1')], considered_paths=checked)
            self.assertEqual([os.path.join(root_dir, 'ws1', 'share', 'foo', 'foopath'),
                              'loc1/foo/foopath',
                              'loc2/foo/foopath',
                              os.path.join(root_dir, 'ws1', 'etc', 'foo', 'foopath')], checked)
            self.assertEqual([], existing)
            checked = []
            existing = find_in_workspaces(['share', 'etc'], 'foo', None, _workspaces=[os.path.join(root_dir, 'ws1')], considered_paths=checked)
            self.assertEqual([os.path.join(root_dir, 'ws1', 'share', 'foo'),
                              'loc1/foo',
                              'loc2/foo',
                              os.path.join(root_dir, 'ws1', 'etc', 'foo')], checked)
            self.assertEqual([os.path.join(root_dir, 'ws1', 'share', 'foo')], existing)
            # first-only option
            checked = []
            existing = find_in_workspaces(None, None, None, _workspaces=[os.path.join(root_dir, 'ws1'), os.path.join(root_dir, 'ws2')], considered_paths=checked)
            self.assertEqual([
                    os.path.join(root_dir, 'ws1', 'include'),
                    os.path.join(root_dir, 'ws1', 'share'),
                    os.path.join(root_dir, 'ws2', 'include'),
                    os.path.join(root_dir, 'ws2', 'share')], existing)
            existing = find_in_workspaces(None, None, None, _workspaces=[os.path.join(root_dir, 'ws1'), os.path.join(root_dir, 'ws2')], considered_paths=checked, first_matching_workspace_only=True)
            self.assertEqual([
                    os.path.join(root_dir, 'ws1', 'include'),
                    os.path.join(root_dir, 'ws1', 'share')], existing)
            existing = find_in_workspaces(None, None, None, _workspaces=[os.path.join(root_dir, 'ws1'), os.path.join(root_dir, 'ws2')], considered_paths=checked, first_match_only=True)
            self.assertEqual([
                    os.path.join(root_dir, 'ws1', 'include')], existing)

            # overlay: first_matching_workspace_only=True
            checked = []
            existing = find_in_workspaces(None, 'foo', None, _workspaces=[os.path.join(root_dir, 'ws1'), os.path.join(root_dir, 'ws2')], considered_paths=checked, first_matching_workspace_only=True)
            self.assertEqual([
                    os.path.join(root_dir, 'ws1', 'include', 'foo'),
                    os.path.join(root_dir, 'ws1', 'share', 'foo')], existing)
        finally:
            alpine.find_in_workspaces.find_projects = fp_backup
            shutil.rmtree(root_dir)