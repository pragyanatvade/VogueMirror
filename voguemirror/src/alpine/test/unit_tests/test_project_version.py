import os
import unittest
import tempfile
import shutil

try:
    from alpine.project_version import _replace_version, update_versions
except ImportError as impe:
    raise ImportError(
        'Please adjust your pythonpath before running this test: %s' % str(impe))


class ProjectVersionTest(unittest.TestCase):

    def test_replace_version(self):
        self.assertEqual("<project><version>0.1.1</version></project>",
                         _replace_version("<project><version>0.1.0</version></project>", "0.1.1"))
        self.assertEqual("<project><version abi='0.1.0'>0.1.1</version></project>",
                         _replace_version("<project><version abi='0.1.0'>0.1.0</version></project>", "0.1.1"))
        self.assertRaises(RuntimeError, _replace_version, "<project></project>", "0.1.1")
        self.assertRaises(RuntimeError, _replace_version, "<project><version>0.1.1</version><version>0.1.1</version></project>", "0.1.1")

    def test_update_versions(self):
        try:
            root_dir = tempfile.mkdtemp()
            sub_dir = os.path.join(root_dir, 'sub')
            with open(os.path.join(root_dir, "project.xml"), 'w') as fhand:
                fhand.write('<project><version>2.3.4</version></project>')
            os.makedirs(os.path.join(sub_dir))
            with open(os.path.join(sub_dir, "project.xml"), 'w') as fhand:
                fhand.write('<project><version>1.5.4</version></project>')

            update_versions([root_dir, sub_dir], "7.6.5")

            with open(os.path.join(root_dir, "project.xml"), 'r') as fhand:
                contents = fhand.read()
                self.assertEqual('<project><version>7.6.5</version></project>', contents)
            with open(os.path.join(sub_dir, "project.xml"), 'r') as fhand:
                contents = fhand.read()
                self.assertEqual('<project><version>7.6.5</version></project>', contents)
        finally:
            shutil.rmtree(root_dir)
