"""
Library to find projects in the filesystem.
"""

import os
from alpine_pkg.project import parse_project, PROJECT_MANIFEST_FILENAME


def find_project_paths(basepath, exclude_paths=None, exclude_subspaces=False):
    """
    Crawls the filesystem to find project manifest files.

    When a subfolder contains a file ``ALPINE_IGNORE`` it is ignored.

    :param basepath: The path to search in, ``str``
    :param exclude_paths: A list of paths which should not be searched, ``list``
    :param exclude_subspaces: The flag is subfolders containing a .alpine file should not be searched, ``bool``
    :returns: A list of relative paths containing project manifest files
    ``list``
    """
    paths = []
    real_exclude_paths = [os.path.realpath(p) for p in exclude_paths] if exclude_paths is not None else []
    for dirpath, dirnames, filenames in os.walk(basepath, followlinks=True):
        if 'ALPINE_IGNORE' in filenames or \
            os.path.realpath(dirpath) in real_exclude_paths or \
            (exclude_subspaces and '.alpine' in filenames):
            del dirnames[:]
            continue
        elif PROJECT_MANIFEST_FILENAME in filenames:
            paths.append(os.path.relpath(dirpath, basepath))
            del dirnames[:]
            continue
        for dirname in dirnames:
            if dirname.startswith('.'):
                dirnames.remove(dirname)
    return paths


def find_projects(basepath, exclude_paths=None, exclude_subspaces=False):
    """
    Crawls the filesystem to find project manifest files and parses them.

    :param basepath: The path to search in, ``str``
    :param exclude_paths: A list of paths which should not be searched, ``list``
    :param exclude_subspaces: The flag is subfolders containing a .alpine file should not be searched, ``bool``
    :returns: A dict mapping relative paths to ``Project`` objects
    ``dict``
    :raises: :exc:RuntimeError` If multiple projects have the same
    name
    """
    projects = {}
    duplicates = {}
    paths = find_project_paths(basepath, exclude_paths, exclude_subspaces)
    for path in paths:
        project = parse_project(os.path.join(basepath, path))
        paths_with_same_name = [path_ for path_, pkg in projects.items() if pkg.name == project.name]
        if paths_with_same_name:
            if project.name not in duplicates:
                duplicates[project.name] = paths_with_same_name
            duplicates[project.name].append(path)
        projects[path] = project
    if duplicates:
        duplicates = ['Multiple projects found with the same name "%s":%s' % (name, ''.join(['\n- %s' % path_ for path_ in paths])) for name, paths in duplicates.items()]
        raise RuntimeError('\n'.join(duplicates))
    return projects


def verify_equal_project_versions(projects):
    """
    Verifies that all projects have the same version number.

    :param projects: The list of ``Project`` objects, ``list``
    :returns: The version number
    :raises: :exc:RuntimeError` If the version is not equal in all
    projects
    """
    version = None
    for project in projects:
        if version is None:
            version = project.version
        elif project.version != version:
            raise RuntimeError('Two projects have different version numbers (%s != %s):\n- %s\n- %s' % (project.version, version, project.filename, projects[0].filename))
    return version
