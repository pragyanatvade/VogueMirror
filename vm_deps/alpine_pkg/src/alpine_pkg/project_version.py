import re


def bump_version(version, bump='patch'):
    """
    Increases version number.

    :param version: str, must be in version format "int.int.int"
    :param bump: str, one of 'patch, minor, major'
    :returns: version with the given part increased, and all inferior parts reset to 0
    :raises ValueError: if the version string is not in the format x.y.z
    """
    # split the version number
    match = re.match('^(\d+)\.(\d+)\.(\d+)$', version)
    if match is None:
        raise ValueError('Invalid version string, must be int.int.int: "%s"' % version)
    new_version = match.groups()
    new_version = [int(x) for x in new_version]
    # find the desired index
    idx = dict(major=0, minor=1, patch=2)[bump]
    # increment the desired part
    new_version[idx] += 1
    # reset all parts behind the bumped part
    new_version = new_version[:idx + 1] + [0 for x in new_version[idx + 1:]]
    return '%d.%d.%d' % tuple(new_version)
