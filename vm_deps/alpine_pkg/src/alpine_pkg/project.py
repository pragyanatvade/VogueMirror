"""
Library for parsing project.xml and providing an object
representation.
"""

from __future__ import print_function

import os
import re
import sys
import xml.dom.minidom as dom

PROJECT_MANIFEST_FILENAME = 'project.xml'


class Project(object):
    """
    Object representation of a project manifest file
    """
    __slots__ = [
        'format',
        'name',
        'version',
        'abi',
        'description',
        'maintainers',
        'licenses',
        'urls',
        'authors',
        'builddeps',
        'buildtooldeps',
        'rundeps',
        'testdeps',
        'conflicts',
        'replaces',
        'exports',
        'filename'
    ]

    def __init__(self, filename=None, **kwargs):
        """
        :param filename: location of project.xml.  Necessary if
          converting ``${prefix}`` in ``<export>`` values, ``str``.
        """
        # initialize all slots ending with "s" with lists, all other with plain values
        for attr in self.__slots__:
            if attr.endswith('s'):
                value = list(kwargs[attr]) if attr in kwargs else []
                setattr(self, attr, value)
            else:
                value = kwargs[attr] if attr in kwargs else None
                setattr(self, attr, value)
        self.filename = filename
        # verify that no unknown keywords are passed
        unknown = set(kwargs.keys()).difference(self.__slots__)
        if unknown:
            raise TypeError('Unknown properties: %s' % ', '.join(unknown))

    def __getitem__(self, key):
        if key in self.__slots__:
            return getattr(self, key)
        raise KeyError('Unknown key "%s"' % key)

    def __iter__(self):
        for slot in self.__slots__:
            yield slot

    def __str__(self):
        data = {}
        for attr in self.__slots__:
            data[attr] = getattr(self, attr)
        return str(data)

    def has_buildtooldep_on_alpine(self):
        """
        Returns True if this Project buildtool depends on alpine, otherwise False

        :returns: True if the given project buildtool depends on alpine
        :rtype: bool
        """
        return 'alpine' in [d.name for d in self.buildtooldeps]


    def has_invalid_metaproject_dependencies(self):
        """
        Returns True if this project has invalid dependencies for a metaproject

        This is defined by REP-0127 as any non-rundeps dependencies other then a buildtooldep on alpine.

        :returns: True if the given project has any invalid dependencies, otherwise False
        :rtype: bool
        """
        buildtooldeps = [d.name for d in self.buildtooldeps if d.name != 'alpine']
        return len(self.builddeps + buildtooldeps + self.testdeps) > 0

    def is_metaproject(self):
        """
        Returns True if this project is a metaproject, otherwise False

        :returns: True if metaproject, else False
        :rtype: bool
        """
        return 'metaproject' in [e.tagname for e in self.exports]

    def validate(self):
        """
        makes sure all standards for projects are met
        :param project: Project to check
        :raises InvalidProject: in case validation fails
        """
        errors = []
        if self.format:
            if not re.match('^[1-9][0-9]*$', str(self.format)):
                errors.append('The "format" attribute of the project must contain a positive integer if present')

        if not self.name:
            errors.append('Project name must not be empty')
        # accepting upper case letters and hyphens only for backward compatibility
        if not re.match('^[a-zA-Z0-9][a-zA-Z0-9_-]*$', self.name):
            errors.append('Project name "%s" does not follow naming conventions' % self.name)
        elif not re.match('^[a-z][a-z0-9_]*$', self.name):
            print('WARNING: Project name "%s" does not follow the naming conventions. It should start with a lower case letter and only contain lower case letters, digits and underscores.' % self.name, file=sys.stderr)

        if not self.version:
            errors.append('Project version must not be empty')
        elif not re.match('^[0-9]+\.[0-9_]+\.[0-9_]+$', self.version):
            errors.append('Project version "%s" does not follow version conventions' % self.version)

        if not self.description:
            errors.append('Project description must not be empty')

        if not self.maintainers:
            errors.append('Project must declare at least one maintainer')
        for maintainer in self.maintainers:
            try:
                maintainer.validate()
            except InvalidProject as e:
                errors.append(str(e))
            if not maintainer.email:
                errors.append('Maintainers must have an email address')

        if not self.licenses:
            errors.append('The project node must contain at least one "license" tag')

        if self.authors is not None:
            for author in self.authors:
                try:
                    author.validate()
                except InvalidProject as e:
                    errors.append(str(e))

        for dep_type, depends in {'build': self.builddeps, 'buildtool': self.buildtooldeps, 'run': self.rundeps, 'test': self.testdeps}.items():
            for depend in depends:
                if depend.name == self.name:
                    errors.append('The project must not "%s_depend" on a project with the same name as this project' % dep_type)

        if self.is_metaproject():
            if not self.has_buildtooldep_on_alpine():
                # TODO escalate to error in the future, or use metaproject.validate_metaproject
                print('WARNING: Metaproject "%s" must buildtooldep on alpine.' % self.name, file=sys.stderr)
            if self.has_invalid_metaproject_dependencies():
                print(('WARNING: Metaproject "%s" should not have other dependencies besides a ' +
                       'buildtooldep on alpine and rundeps.') % self.name, file=sys.stderr)

        if errors:
            raise InvalidProject('\n'.join(errors))


class Dependency(object):
    __slots__ = ['name', 'lt', 'lte', 'eq', 'gte', 'gt']

    def __init__(self, name, **kwargs):
        for attr in self.__slots__:
            value = kwargs[attr] if attr in kwargs else None
            setattr(self, attr, value)
        self.name = name
        # verify that no unknown keywords are passed
        unknown = set(kwargs.keys()).difference(self.__slots__)
        if unknown:
            raise TypeError('Unknown properties: %s' % ', '.join(unknown))

    def __str__(self):
        return self.name


class Export(object):
    __slots__ = ['tagname', 'attributes', 'content']

    def __init__(self, tagname, content=None):
        self.tagname = tagname
        self.attributes = {}
        self.content = content

    def __str__(self):
        txt = '<%s' % self.tagname
        for key in sorted(self.attributes.keys()):
            txt += ' %s="%s"' % (key, self.attributes[key])
        if self.content:
            txt += '>%s</%s>' % (self.content, self.tagname)
        else:
            txt += '/>'
        return txt


class Person(object):
    __slots__ = ['name', 'email']

    def __init__(self, name, email=None):
        self.name = name
        self.email = email

    def __str__(self):
        name = self.name
        if not isinstance(name, str):
            name = name.encode('utf-8')
        if self.email is not None:
            return '%s <%s>' % (name, self.email)
        else:
            return '%s' % name

    def validate(self):
        if self.email is None:
            return
        if not re.match('^[a-zA-Z0-9._%\+-]+@[a-zA-Z0-9._%-]+\.[a-zA-Z]{2,6}$', self.email):
            raise InvalidProject('Invalid email "%s" for person "%s"' % (self.email, self.name))


class Url(object):
    __slots__ = ['url', 'type']

    def __init__(self, url, type_=None):
        self.url = url
        self.type = type_

    def __str__(self):
        return self.url


def parse_project_for_distutils(path=None):
    print('WARNING: %s/setup.py: alpine_pkg.project.parse_project_for_distutils() is deprecated. Please use alpine_pkg.python_setup.generate_distutils_setup(**kwargs) instead.' % os.path.basename(os.path.abspath('.')))
    from .python_setup import generate_distutils_setup
    data = {}
    if path is not None:
        data['project_xml_path'] = path
    return generate_distutils_setup(**data)


class InvalidProject(Exception):
    pass


def project_exists_at(path):
    """
    Checks that a project exists at the given path

    :param path: path to a project
    :type path: str
    :returns: True if project exists in given path, else False
    :rtype: bool
    """
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, PROJECT_MANIFEST_FILENAME))


def parse_project(path):
    """
    Parse project manifest.

    :param path: The path of the project.xml file, it may or may not
    include the filename

    :returns: return :class:`Project` instance, populated with parsed fields
    :raises: :exc:`InvalidProject`
    :raises: :exc:`IOError`
    """
    if os.path.isfile(path):
        filename = path
    elif project_exists_at(path):
        filename = os.path.join(path, PROJECT_MANIFEST_FILENAME)
        if not os.path.isfile(filename):
            raise IOError('Directory "%s" does not contain a "%s"' % (path, PROJECT_MANIFEST_FILENAME))
    else:
        raise IOError('Path "%s" is neither a directory containing a "%s" file nor a file' % (path, PROJECT_MANIFEST_FILENAME))

    with open(filename, 'r') as f:
        try:
            return parse_project_string(f.read(), filename)
        except InvalidProject as e:
            e.args = ['Invalid project manifest "%s": %s' % (filename, e.message)]
            raise


def parse_project_string(data, filename=None):
    """
    Parse project.xml string contents.

    :param data: project.xml contents, ``str``
    :param filename: full file path for debugging, ``str``
    :returns: return parsed :class:`Project`
    :raises: :exc:`InvalidProject`
    """
    try:
        d = dom.parseString(data)
    except Exception as e:
        raise InvalidProject('The manifest contains invalid XML:\n%s' % e)

    pkg = Project(filename)

    # verify unique root node
    nodes = _get_nodes(d, 'project')
    if len(nodes) != 1:
        raise InvalidProject('The manifest must contain a single "project" root tag')
    root = nodes[0]

    # format attribute
    value = _get_node_attr(root, 'format', default=1)
    pkg.format = int(value)

    # name
    pkg.name = _get_node_value(_get_node(root, 'name'))

    # version and optional abi
    version_node = _get_node(root, 'version')
    pkg.version = _get_node_value(version_node)
    pkg.abi = _get_node_attr(version_node, 'abi', default=None)

    # description
    pkg.description = _get_node_value(_get_node(root, 'description'), allow_xml=True, apply_str=False)

    # at least one maintainer, all must have email
    maintainers = _get_nodes(root, 'maintainer')
    for node in maintainers:
        pkg.maintainers.append(Person(
            _get_node_value(node, apply_str=False),
            _get_node_attr(node, 'email')
        ))

    # urls with optional type
    urls = _get_nodes(root, 'url')
    for node in urls:
        pkg.urls.append(Url(
            _get_node_value(node),
            _get_node_attr(node, 'type', default='website')
        ))

    # authors with optional email
    authors = _get_nodes(root, 'author')
    for node in authors:
        pkg.authors.append(Person(
            _get_node_value(node, apply_str=False),
            _get_node_attr(node, 'email', default=None)
        ))

    # at least one license
    licenses = _get_nodes(root, 'license')
    for node in licenses:
        pkg.licenses.append(_get_node_value(node))

    # dependencies and relationships
    pkg.builddeps = _get_dependencies(root, 'builddep')
    pkg.buildtooldeps = _get_dependencies(root, 'buildtooldep')
    pkg.rundeps = _get_dependencies(root, 'rundep')
    pkg.testdeps = _get_dependencies(root, 'testdep')
    pkg.conflicts = _get_dependencies(root, 'conflict')
    pkg.replaces = _get_dependencies(root, 'replace')

    errors = []
    for testdep in pkg.testdeps:
        same_builddeps = ['builddep' for d in pkg.builddeps if d.name == testdep.name]
        same_rundeps = ['rundep' for d in pkg.rundeps if d.name == testdep.name]
        if same_builddeps or same_rundeps:
            errors.append('The test dependency on "%s" is redundant with: %s' % (testdep.name, ', '.join(same_builddeps + same_rundeps)))

    # exports
    export_node = _get_optional_node(root, 'export')
    if export_node is not None:
        exports = []
        for node in [n for n in export_node.childNodes if n.nodeType == n.ELEMENT_NODE]:
            export = Export(str(node.tagName), _get_node_value(node, allow_xml=True))
            for key, value in node.attributes.items():
                export.attributes[str(key)] = str(value)
            exports.append(export)
        pkg.exports = exports

    # verify that no unsupported tags and attributes are present
    unknown_root_attributes = [attr for attr in root.attributes.keys() if str(attr) != 'format']
    if unknown_root_attributes:
        errors.append('The "project" tag must not have the following attributes: %s' % ', '.join(unknown_root_attributes))
    depend_attributes = ['lt', 'lte', 'eq', 'gte', 'gt']
    known = {
        'name': [],
        'version': ['abi'],
        'description': [],
        'maintainer': ['email'],
        'license': [],
        'url': ['type'],
        'author': ['email'],
        'builddep': depend_attributes,
        'buildtooldep': depend_attributes,
        'rundep': depend_attributes,
        'testdep': depend_attributes,
        'conflict': depend_attributes,
        'replace': depend_attributes,
        'export': [],
    }
    nodes = [n for n in root.childNodes if n.nodeType == n.ELEMENT_NODE]
    unknown_tags = set([n.tagName for n in nodes if n.tagName not in known.keys()])
    if unknown_tags:
        errors.append('The manifest must not contain the following tags: %s' % ', '.join(unknown_tags))
    for node in [n for n in nodes if n.tagName in known.keys()]:
        unknown_attrs = [str(attr) for attr in node.attributes.keys() if str(attr) not in known[node.tagName]]
        if unknown_attrs:
            errors.append('The "%s" tag must not have the following attributes: %s' % (node.tagName, ', '.join(unknown_attrs)))
        if node.tagName not in ['description', 'export']:
            subnodes = [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE]
            if subnodes:
                errors.append('The "%s" tag must not contain the following children: %s' % (node.tagName, ', '.join([n.tagName for n in subnodes])))

    if errors:
        raise InvalidProject('Error(s) in %s:%s' % (filename, ''.join(['\n- %s' % e for e in errors])))

    pkg.validate()

    return pkg


def _get_nodes(parent, tagname):
    return [n for n in parent.childNodes if n.nodeType == n.ELEMENT_NODE and n.tagName == tagname]


def _get_node(parent, tagname):
    nodes = _get_nodes(parent, tagname)
    if len(nodes) != 1:
        raise InvalidProject('The manifest must contain exactly one "%s" tags' % tagname)
    return nodes[0]


def _get_optional_node(parent, tagname):
    nodes = _get_nodes(parent, tagname)
    if len(nodes) > 1:
        raise InvalidProject('The manifest must not contain more than one "%s" tags' % tagname)
    return nodes[0] if nodes else None


def _get_node_value(node, allow_xml=False, apply_str=True):
    if allow_xml:
        value = (''.join([n.toxml() for n in node.childNodes])).strip(' \n\r\t')
    else:
        value = (''.join([n.data for n in node.childNodes if n.nodeType == n.TEXT_NODE])).strip(' \n\r\t')
    if apply_str:
        value = str(value)
    return value


def _get_optional_node_value(parent, tagname, default=None):
    node = _get_optional_node(parent, tagname)
    if node is None:
        return default
    return _get_node_value(node)


def _get_node_attr(node, attr, default=False):
    """
    :param default: False means value is required
    """
    if node.hasAttribute(attr):
        return str(node.getAttribute(attr))
    if default is False:
        raise InvalidProject('The "%s" tag must have the attribute "%s"' % (node.tagName, attr))
    return default


def _get_dependencies(parent, tagname):
    depends = []
    for node in _get_nodes(parent, tagname):
        depend = Dependency(_get_node_value(node))
        for attr in ['lt', 'lte', 'eq', 'gte', 'gt']:
            setattr(depend, attr, _get_node_attr(node, attr, None))
        depends.append(depend)
    return depends
