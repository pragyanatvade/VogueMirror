#!/usr/bin/env python

from __future__ import print_function
import sys
import argparse

try:
    from alpine_pkg.project import parse_project
except ImportError as e:
    sys.exit('ImportError: "from alpine_pkg.project import parse_project" failed: %s\nMake sure that you have installed "alpine_pkg", it is up to date and on the PYTHONPATH.' % e)


def _get_output(project):
    """
    returns a list of strings with cmake commands to execute to set cmake variables

    :param project: Project object
    :returns: list of str, lines to output
    """
    values = {}
    values['VERSION'] = '"%s"' % project.version

    values['MAINTAINER'] = '"%s"' % (', '.join([str(m) for m in project.maintainers]))

    values.update(_get_dependency_values('BUILDDEPS', project.builddeps))
    values.update(_get_dependency_values('BUILDTOOLDEPS', project.buildtooldeps))
    values.update(_get_dependency_values('RUNDEPS', project.rundeps))

    deprecated = [e.content for e in project.exports if e.tagname == 'deprecated']
    values['DEPRECATED'] = '"%s"' % ((deprecated[0] if deprecated[0] else 'TRUE') if deprecated else '')

    output = []
    output.append(r'set(_ALPINE_CURRENT_PROJECT "%s")' % project.name)
    for k, v in values.items():
        output.append('set(%s_%s %s)' % (project.name, k, v))
    return output

def _get_dependency_values(key, depends):
    values = {}
    values[key] = ' '.join(['"%s"' % str(d) for d in depends])
    for d in depends:
        comparisons = ['lt', 'lte', 'eq', 'gte', 'gt']
        for comp in comparisons:
            value = getattr(d, comp, None)
            if value is not None:
                values['%s_%s_%s' % (key, str(d), comp.upper())] = '"%s"' % value
    return values


def main(argv=sys.argv[1:]):
    """
    Reads given project_xml and writes extracted variables to outfile.
    """
    parser = argparse.ArgumentParser(description="Read project.xml and write extracted variables to stdout")
    parser.add_argument('project_xml')
    parser.add_argument('outfile')
    args = parser.parse_args(argv)
    project = parse_project(args.project_xml)

    lines = _get_output(project)
    with open(args.outfile, 'w') as ofile:
        ofile.write('\n'.join(lines))


if __name__ == '__main__':
    main()
