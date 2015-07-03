#!/usr/bin/env python

from distutils.core import setup
from alpine_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['alpine'],
    package_dir={'': 'python'},
    scripts=[
        'scripts/alpine_find',
        'scripts/alpine_init_workspace',
        'scripts/alpine_make',
        'scripts/alpine_make_isolated',
        'scripts/alpine_project_version',
        'scripts/alpine_prepare_release',
        'scripts/alpine_test_results',
        'scripts/alpine_topological_order',
    ],
)

setup(**d)
