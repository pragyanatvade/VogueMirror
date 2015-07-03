#
# It installs the project.xml file of a metaproject.
#
# .. note:: It must be called once for each metaproject.  Best
#   practice is to call this macro early in your root CMakeLists.txt,
#   immediately after calling ``project()`` and
#   ``find_package(alpine REQUIRED)``.
#
# :param DIRECTORY: the path to the project.xml file if not in the same
#   location as the CMakeLists.txt file
# :type DIRECTORY: string
#
# @public
#
function(alpine_metaproject)
  cmake_parse_arguments(ARG "" "DIRECTORY" "" ${ARGN})
  if(ARG_UNPARSED_ARGUMENTS)
    message(FATAL_ERROR "alpine_metaproject() called with unused arguments: ${ARG_UNPARSED_ARGUMENTS}")
  endif()

  # verify that project() has been called before
  if(NOT PROJECT_NAME)
    message(FATAL_ERROR "alpine_metaproject() PROJECT_NAME is not set. You must call project() before calling alpine_metaproject().")
  endif()
  if(PROJECT_NAME STREQUAL "Project")
    message(FATAL_ERROR "alpine_metaproject() PROJECT_NAME is set to 'Project', which is not a valid project name. You must call project() before calling alpine_metaproject().")
  endif()

  debug_message(10 "alpine_metaproject() called in file ${CMAKE_CURRENT_LIST_FILE}")

  if(NOT ARG_DIRECTORY)
    if(${CMAKE_CURRENT_LIST_FILE} STREQUAL ${CMAKE_BINARY_DIR}/alpine_generated/metaprojects/${PROJECT_NAME}/CMakeLists.txt)
      set(ARG_DIRECTORY ${CMAKE_SOURCE_DIR}/${path})
    else()
      set(ARG_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
    endif()
  endif()

  alpine_project_xml(DIRECTORY ${ARG_DIRECTORY})

  # install project.xml
  install(FILES ${ARG_DIRECTORY}/project.xml
    DESTINATION share/${PROJECT_NAME}
  )
endfunction()
