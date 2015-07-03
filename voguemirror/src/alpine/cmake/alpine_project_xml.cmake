#
# Parse project.xml from ``CMAKE_CURRENT_SOURCE_DIR`` and
# make several information available to CMake.
#
# .. note:: It is called automatically by ``alpine_project()`` if not
#   called manually before.  It must be called once in each package,
#   after calling ``project()`` where the project name must match the
#   package name.  The macro should only be called manually if the
#   variables are use to parameterize ``alpine_project()``.
#
# :param DIRECTORY: the directory of the project.xml (default
#   ``${CMAKE_CURRENT_SOURCE_DIR}``).
# :type DIRECTORY: string
#
# :outvar <packagename>_VERSION: the version number
# :outvar <packagename>_MAINTAINER: the name and email of the
#   maintainer(s)
# :outvar _ALPINE_CURRENT_PROJECT: the name of the package from the
#   manifest
#
# .. note:: It is calling ``alpine_destinations()`` which will provide
#   additional output variables.
#
# @public
#
macro(alpine_project_xml)
  debug_message(10 "alpine_project_xml()")

  # verify that project() has been called before
  if(NOT PROJECT_NAME)
    message(FATAL_ERROR "alpine_project_xml() PROJECT_NAME is not set. You must call project() before you can call alpine_project_xml().")
  endif()

  # ensure that function is not called multiple times per package
  if(DEFINED _ALPINE_CURRENT_PROJECT)
    message(FATAL_ERROR "alpine_project_xml(): in '${CMAKE_CURRENT_LIST_FILE}', _ALPINE_CURRENT_PROJECT is already set (to: ${_ALPINE_CURRENT_PROJECT}).  Did you called alpine_project_xml() multiple times?")
  endif()

  _alpine_project_xml(${CMAKE_CURRENT_BINARY_DIR}/alpine_generated ${ARGN})

  # verify that the package name from project.xml equals the project() name
  if(NOT _ALPINE_CURRENT_PROJECT STREQUAL PROJECT_NAME)
    message(FATAL_ERROR "alpine_project_xml() package name '${_ALPINE_CURRENT_PROJECT}'  in '${_PROJECT_XML_DIRECTORY}/project.xml' does not match current PROJECT_NAME '${PROJECT_NAME}'.  You must call project() with the same package name before.")
  endif()

  alpine_destinations()
endmacro()

macro(_alpine_project_xml dest_dir)
  cmake_parse_arguments(_PROJECT_XML "" "DIRECTORY" "" ${ARGN})
  if(_PROJECT_XML_UNPARSED_ARGUMENTS)
    message(FATAL_ERROR "alpine_project_xml() called with unused arguments: ${_PROJECT_XML_UNPARSED_ARGUMENTS}")
  endif()

  # set default directory
  if(NOT _PROJECT_XML_DIRECTORY)
    set(_PROJECT_XML_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
  endif()

  # stamp and parse project.xml
  stamp(${_PROJECT_XML_DIRECTORY}/project.xml)
  file(MAKE_DIRECTORY ${dest_dir})
  safe_execute_process(COMMAND ${PYTHON_EXECUTABLE}
    ${alpine_EXTRAS_DIR}/parse_project_xml.py
    ${_PROJECT_XML_DIRECTORY}/project.xml
    ${dest_dir}/package.cmake)
  # load extracted variable into cmake
  include(${dest_dir}/package.cmake)
endmacro()
