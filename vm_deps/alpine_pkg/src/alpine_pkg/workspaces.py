"""
Library to provided logic for chained workspaces
"""

from __future__ import print_function

import os


def get_spaces(paths=None):
    """
    Return a list of spaces based on the CMAKE_PREFIX_PATH or passed in list of workspaces.
    It resolves the source space for each devel space and ignores non-alpine paths.
    :param paths_to_order: list of paths
    :param prefix_paths: list of prefixes, must not end with '/'
    """
    if paths is None:
        if 'CMAKE_PREFIX_PATH' not in os.environ:
            raise RuntimeError('Neither the environment variable CMAKE_PREFIX_PATH is set nor was a list of paths passed.')
        paths = os.environ['CMAKE_PREFIX_PATH'].split(os.pathsep) if os.environ['CMAKE_PREFIX_PATH'] else []

    spaces = []
    for path in paths:
        marker = os.path.join(path, '.alpine')
        # ignore non alpine paths
        if not os.path.exists(marker):
            continue
        spaces.append(path)

        # append source spaces
        with open(marker, 'r') as f:
            data = f.read()
            if data:
                spaces += data.split(';')
    return spaces


def order_paths(paths_to_order, prefix_paths):
    """
    Return a list containing all items of paths_to_order ordered by list of prefix_paths, compared as strings
    :param paths_to_order: list of paths
    :param prefix_paths: list of prefixes, must not end with '/'
    """
    # the ordered paths contains a list for each prefix plus one more which contains paths which do not match one of the prefix_paths
    ordered_paths = [[] for _ in range(len(prefix_paths) + 1)]

    for path in paths_to_order:
        # put each directory into the slot where it matches the prefix, or last otherwise
        index = 0
        for prefix in prefix_paths:
            if path == prefix or path.startswith(prefix + os.sep) or (os.altsep and path.startswith(prefix + os.altsep)):
                break
            index += 1
        ordered_paths[index].append(path)

    # flatten list of lists
    return [j for i in ordered_paths for j in i]
