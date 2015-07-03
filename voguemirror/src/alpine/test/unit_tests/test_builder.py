# -*- coding: utf-8 -*-

import os
import unittest

try:
    import alpine.builder
except ImportError as e:
    raise ImportError(
        'Please adjust your pythonpath before running this test: %s' % str(e)
    )


class BuilderTest(unittest.TestCase):
    # TODO: Add tests for alpine_make and alpine_make_isolated

    def test_run_command_unicode(self):
        backup_Popen = alpine.builder.subprocess.Popen

        class StdOut(object):
            def __init__(self, popen):
                self.__popen = popen

            def readline(self):
                self.__popen.returncode = 0
                try:
                    # for Python 2 compatibility only
                    return unichr(2018)
                except NameError:
                    return chr(2018)

        class MockPopen(object):
            def __init__(self, *args, **kwargs):
                self.returncode = None
                self.stdout = StdOut(self)

            def wait(self):
                return True

        try:
            alpine.builder.subprocess.Popen = MockPopen
            alpine.builder.run_command(['false'], os.getcwd(), True, True)
        finally:
            alpine.builder.subprocess.Popen = backup_Popen

    def test_extract_jobs_flags(self):
        valid_mflags = [
            '-j8 -l8', 'j8 ', '-j', 'j', '-l8', 'l8',
            '-l', 'l', '-j18', ' -j8 l9', '-j1 -l1',
            '--jobs=8', '--jobs 8', '--jobs', '--load-average',
            '--load-average=8', '--load-average 8', '--jobs=8 -l9'
        ]
        results = [
            '-j8 -l8', 'j8', '-j', 'j', '-l8', 'l8',
            '-l', 'l', '-j18', '-j8 l9', '-j1 -l1',
            '--jobs=8', '--jobs 8', '--jobs', '--load-average',
            '--load-average=8', '--load-average 8', '--jobs=8 -l9'
        ]
        for mflag, result in zip(valid_mflags, results):
            match = alpine.builder.extract_jobs_flags(mflag)
            assert match == result, "should match '{0}'".format(mflag)
            print('--')
            print("input:    '{0}'".format(mflag))
            print("matched:  '{0}'".format(match))
            print("expected: '{0}'".format(result))
        invalid_mflags = ['', '--jobs= 8', '--jobs8']
        for mflag in invalid_mflags:
            match = alpine.builder.extract_jobs_flags(mflag)
            assert match is None, "should not match '{0}'".format(mflag)
