#!/usr/bin/env python

from distutils.core import setup

import os
import sys
source = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, source)

from alpine_pkg import __version__

setup(
    name='alpine_pkg',
    version=__version__,
    packages=['alpine_pkg'],
    package_dir={'': 'src'},
    package_data={'alpine_pkg': ['templates/*.in']},
    scripts=[
        'scripts/alpine_create_project',
        'scripts/alpine_find_project',
        'scripts/alpine_generate_changelog',
        'scripts/alpine_tag_changelog',
        'scripts/alpine_test_changelog',
    ],
    author='Pragyan',
    author_email='pragyan@voguemirror.com',
    url='https://github.com/pntripathi9417/voguemirror/wiki/alpine_pkg',
    download_url='https://github.com/pntripathi9417/vm_deps',
    keywords=['alpine'],
    classifiers=[
        'Programming Language :: Python',
    ],
    description='alpine project library',
    long_description='Library for retrieving information about alpine projects.',
    license='Voguemirror Proprietary',
    install_requires=[
        'argparse',
        'docutils',
        'python-dateutil'
    ],
)