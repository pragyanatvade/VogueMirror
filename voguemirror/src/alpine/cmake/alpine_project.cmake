#
# It installs the project.xml file, and it generates code for
# ``find_package`` and ``pkg-config`` so that other packages can get
# information about this package.  For this purpose the information
# about include directories, libraries, further dependencies and
# CMake variables are used.
#
# .. note:: It must be called once for each package.  It is indirectly
#   calling``alpine_destinations()`` which will provide additional
#   output variables.  Please make sure to call ``alpine_project()``
#   before using those variables.
#
# :param INCLUDE_DIRS: ``CMAKE_CURRENT_SOURCE_DIR``-relative paths to
#   C/C++ includes
# :type INCLUDE_DIRS: list of strings
# :param LIBRARIES: names of library targets that will appear in the
#   ``alpine_LIBRARIES`` and ``${PROJECT_NAME}_LIBRARIES`` of other
#   projects that search for you via ``find_package``.  Currently
#   this will break if the logical target names are not the same as
#   the installed names.
# :type LIBRARIES: list of strings
# :param ALPINE_DEPENDS: a list of alpine projects which this project
#   depends on.  It is used when client code finds this project via
#   ``find_package()`` or ``pkg-config``.  Each project listed will in
#   turn be ``find_package``\ -ed or is states as ``Requires`` in the
#   .pc file.  Therefore their ``INCLUDE_DIRS`` and ``LIBRARIES`` will
#   be appended to ours.  Only alpine projects should be used where it
#   be guarantee that they are *find_packagable* and have pkg-config
#   files.
# :type ALPINE_DEPENDS: list of strings
# :param DEPENDS: a list of CMake projects which this project depends
#   on.  Since they might not be *find_packagable* or lack a pkg-config
#   file their ``INCLUDE_DIRS`` and ``LIBRARIES`` are passed directly.
#   This requires that it has been ``find_package``\ -ed before.
# :type DEPENDS: list of strings
# :param CFG_EXTRAS: a CMake file containing extra stuff that should
#   be accessible to users of this package after
#   ``find_package``\ -ing it.  This file must live in the
#   subdirectory ``cmake`` or be an absolute path.  Various additional
#   file extension are possible:
#   for a plain cmake file just ``.cmake``, for files expanded using
#   CMake's ``configure_file()`` use ``.cmake.in`` or for files expanded
#   by empy use ``.cmake.em``.  The templates can distinguish between
#   devel- and installspace using the boolean variables ``DEVELSPACE``
#   and ``INSTALLSPACE``.  For templated files it is also possible to
#   use the extensions ``.cmake.develspace.(in|em)`` or
#   ``.cmake.installspace.(em|in)`` to generate the files only for a
#   specific case.
#   If the global variable ${PROJECT_NAME}_CFG_EXTRAS is set it will be
#   prepended to the explicitly passed argument.
# :type CFG_EXTRAS: string
# :param EXPORTED_TARGETS: a list of target names which usually generate
#   code. Downstream packages can depend on these targets to ensure that
#   code is generated before it is being used. The generated CMake config
#   file will ensure that the targets exists.
#   If the global variable ${PROJECT_NAME}_EXPORTED_TARGETS is
#   set it will be prepended to the explicitly passed argument.
# :type EXPORTED_TARGETS: list of string
# :param SKIP_CMAKE_CONFIG_GENERATION: the option to skip the generation
#   of the CMake config files for the package
# :type SKIP_CMAKE_CONFIG_GENERATION: bool
# :param SKIP_PKG_CONFIG_GENERATION: the option to skip the generation of
#   the pkg-config file for the package
# :type SKIP_PKG_CONFIG_GENERATION: bool
#
# Example:
# ::
#
#   alpine_project(
#     INCLUDE_DIRS include
#     LIBRARIES projlib1 projlib2
#     ALPINE_DEPENDS cpp
#     DEPENDS Eigen
#     CFG_EXTRAS proj-extras[.cmake|.cmake.in|.cmake(.develspace|.installspace)?.em]
#   )
#
# @public
#
macro(alpine_project)
  debug_message(10 "alpine_project() called in file ${CMAKE_CURRENT_LIST_FILE}")

  # verify that project() has been called before
  if(NOT PROJECT_NAME)
    message(FATAL_ERROR "alpine_project() PROJECT_NAME is not set. You must call project() before calling alpine_project().")
  endif()
  if(PROJECT_NAME STREQUAL "Project")
    message(FATAL_ERROR "alpine_project() PROJECT_NAME is set to 'Project', which is not a valid project name. You must call project() before calling alpine_project().")
  endif()

  # mark that alpine_project() was called in order to detect wrong order of calling with generate_messages()
  set(${PROJECT_NAME}_ALPINE_PROJECT TRUE)

  # call alpine_project_xml() if it has not been called before
  if(NOT _ALPINE_CURRENT_PROJECT)
    alpine_project_xml()
  endif()

  _alpine_project(${ARGN})
endmacro()

function(_alpine_project)
  cmake_parse_arguments(PROJECT "SKIP_CMAKE_CONFIG_GENERATION;SKIP_PKG_CONFIG_GENERATION" "" "INCLUDE_DIRS;LIBRARIES;ALPINE_DEPENDS;DEPENDS;CFG_EXTRAS; EXPORTED_TARGETS" ${ARGN})
  if(PROJECT_UNPARSED_ARGUMENTS)
    message(FATAL_ERROR "alpine_project() called with unused arguments: ${PROJECT_UNPARSED_ARGUMENTS}")
  endif()

  if(NOT ${PROJECT_NAME} STREQUAL "alpine")
    list(FIND ${PROJECT_NAME}_BUILDTOOLDEPS "alpine" _index)
    if(_index EQUAL -1)
      list(FIND ${PROJECT_NAME}_BUILDDEPS "alpine" _index)
      if(_index EQUAL -1)
        message(FATAL_ERROR "alpine_project() 'alpine' must be listed as a buildtool dependency in the project.xml")
      endif()
      message("WARNING: 'alpine' should be listed as a buildtool dependency in the project.xml (instead of build dependency)")
    endif()
  endif()

  # prepend INCLUDE_DIRS passed using a variable
  if(${PROJECT_NAME}_INCLUDE_DIRS)
    list(INSERT PROJECT_INCLUDE_DIRS 0 ${${PROJECT_NAME}_INCLUDE_DIRS})
  endif()

  # unset previously found directory of this package, so that this package overlays the other cleanly
  if(${PROJECT_NAME}_DIR)
    set(${PROJECT_NAME}_DIR "" CACHE PATH "" FORCE)
  endif()

  set(_PROJECT_ALPINE_DEPENDS ${PROJECT_ALPINE_DEPENDS})

  set(PROJECT_DEPENDENCIES_INCLUDE_DIRS "")
  set(PROJECT_DEPENDENCIES_LIBRARIES "")
  foreach(depend ${PROJECT_DEPENDS})
    string(REPLACE " " ";" depend_list ${depend})
    # check if the second argument is the COMPONENTS keyword
    list(LENGTH depend_list count)
    set(second_item "")
    if(${count} GREATER 1)
      list(GET depend_list 1 second_item)
    endif()
    if("${second_item}" STREQUAL "COMPONENTS")
      list(GET depend_list 0 depend_name)
      if(NOT ${${depend_name}_FOUND})
        message(FATAL_ERROR "alpine_project() DEPENDS on '${depend}' which must be find_package()-ed before")
      endif()
      message(WARNING "alpine_project() DEPENDS on '${depend}' which is deprecated. find_package() it before and only DEPENDS on '${depend_name}' instead")
      list(APPEND PROJECT_DEPENDENCIES_INCLUDE_DIRS ${${depend_name}_INCLUDE_DIRS})
      list(APPEND PROJECT_DEPENDENCIES_LIBRARIES ${${depend_name}_LIBRARIES})
    else()
      # split multiple names (without COMPONENTS) into separate dependencies
      foreach(depend_name ${depend_list})
        if(${depend_name}_FOUND_ALPINE_PROJECT)
          #message(WARNING "alpine_project() DEPENDS on alpine project '${depend_name}' which is deprecated. Use ALPINE_DEPENDS for alpine projects instead.")
          list(APPEND _PROJECT_ALPINE_DEPENDS ${depend_name})
        else()
          if(NOT ${${depend_name}_FOUND})
            message(FATAL_ERROR "alpine_project() DEPENDS on '${depend_name}' which must be find_package()-ed before. If it is a alpine project it can be declared as ALPINE_DEPENDS instead without find_package()-ing it.")
          endif()
          list(APPEND PROJECT_DEPENDENCIES_INCLUDE_DIRS ${${depend_name}_INCLUDE_DIRS})
          list(APPEND PROJECT_DEPENDENCIES_LIBRARIES ${${depend_name}_LIBRARIES})
        endif()
      endforeach()
    endif()
  endforeach()

  # for alpine projects it can be guaranteed that they are find_package()-able and have pkg-config files
  set(PROJECT_DEPENDENCIES "")
  foreach(depend_name ${_PROJECT_ALPINE_DEPENDS})
    # verify that all alpine projects which have been find_package()-ed are listed as build dependencies
    if(${depend_name}_FOUND)
      # verify that these packages are really alpine projects
      if(NOT ${depend_name}_FOUND_ALPINE_PROJECT)
        if(DEFINED ${depend_name}_CONFIG)
          message(FATAL_ERROR "alpine_project() ALPINE_DEPENDS on '${depend_name}', which has been found in '${${depend_name}_CONFIG}', but it is not a alpine project")
        else()
          message(FATAL_ERROR "alpine_project() ALPINE_DEPENDS on '${depend_name}', but it is not a alpine project")
        endif()
      endif()
      if(alpine_ALL_FOUND_COMPONENTS)
        list(FIND alpine_ALL_FOUND_COMPONENTS ${depend_name} _index)
      else()
        set(_index -1)
      endif()
      if(NOT _index EQUAL -1)
        list(FIND ${PROJECT_NAME}_BUILDDEPS ${depend_name} _index)
        if(_index EQUAL -1)
          message(FATAL_ERROR "alpine_project() the alpine project '${depend_name}' has been find_package()-ed but is not listed as a build dependency in the project.xml")
        endif()
        # verify versioned dependency constraints
        if(DEFINED ${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_LT AND
            NOT "${${depend_name}_VERSION}" VERSION_LESS "${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_LT}")
          message(WARNING "alpine_project() version mismatch: the project.xml of '${PROJECT_NAME}' builddeps on '${depend_name} < ${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_LT}', but '${depend_name} ${${depend_name}_VERSION}' found")
        endif()
        if(DEFINED ${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_LTE AND
            "${${depend_name}_VERSION}" VERSION_GREATER "${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_LTE}")
          message(WARNING "alpine_project() version mismatch: the project.xml of '${PROJECT_NAME}' builddeps on '${depend_name} <= ${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_LTE}', but '${depend_name} ${${depend_name}_VERSION}' found")
        endif()
        if(DEFINED ${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_EQ AND
            NOT "${${depend_name}_VERSION}" VERSION_EQUAL "${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_EQ}")
          message(WARNING "alpine_project() version mismatch: the project.xml of '${PROJECT_NAME}' builddeps on '${depend_name} = ${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_EQ}', but '${depend_name} ${${depend_name}_VERSION}' found")
        endif()
        if(DEFINED ${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_GTE AND
            "${${depend_name}_VERSION}" VERSION_LESS "${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_GTE}")
          message(WARNING "alpine_project() version mismatch: the project.xml of '${PROJECT_NAME}' builddeps on '${depend_name} >= ${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_GTE}', but '${depend_name} ${${depend_name}_VERSION}' found")
        endif()
        if(DEFINED ${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_GT AND
            NOT "${${depend_name}_VERSION}" VERSION_GREATER "${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_GT}")
          message(WARNING "alpine_project() version mismatch: the project.xml of '${PROJECT_NAME}' builddeps on '${depend_name} > ${${PROJECT_NAME}_BUILDDEPS_${depend_name}_VERSION_GT}', but '${depend_name} ${${depend_name}_VERSION}' found")
        endif()
      endif()
    endif()
    # verify that all alpine projects are listed as run dependencies
    list(FIND ${PROJECT_NAME}_RUNDEPS ${depend_name} _index)
    if(_index EQUAL -1)
      message(FATAL_ERROR "alpine_project() DEPENDS on the alpine project '${depend_name}' which must therefore be listed as a run dependency in the project.xml")
    endif()
    list(APPEND PROJECT_DEPENDENCIES ${depend_name})
  endforeach()

  # package version provided by package.cmake/xml
  set(PROJECT_VERSION ${${PROJECT_NAME}_VERSION})

  # flag if package is deprecated provided by package.cmake/xml
  set(PROJECT_DEPRECATED ${${PROJECT_NAME}_DEPRECATED})

  # package maintainer provided by package.cmake/xml
  set(PROJECT_MAINTAINER ${${PROJECT_NAME}_MAINTAINER})

  # get library paths from all workspaces
  set(lib_paths "")
  foreach(workspace ${ALPINE_WORKSPACES})
    list_append_unique(lib_paths ${workspace}/lib)
  endforeach()

  # merge explicitly listed libraries and libraries from non-alpine but find_package()-ed packages
  set(_PKG_CONFIG_LIBRARIES "")
  if(PROJECT_LIBRARIES)
    list(APPEND _PKG_CONFIG_LIBRARIES ${PROJECT_LIBRARIES})
  endif()
  if(PROJECT_DEPENDENCIES_LIBRARIES)
    list(APPEND _PKG_CONFIG_LIBRARIES ${PROJECT_DEPENDENCIES_LIBRARIES})
  endif()

  # resolve imported library targets
  alpine_replace_imported_library_targets(_PKG_CONFIG_LIBRARIES ${_PKG_CONFIG_LIBRARIES})

  # deduplicate libraries while maintaining build configuration keywords
  alpine_pack_libraries_with_build_configuration(_PKG_CONFIG_LIBRARIES ${_PKG_CONFIG_LIBRARIES})
  set(PKG_CONFIG_LIBRARIES "")
  foreach(library ${_PKG_CONFIG_LIBRARIES})
    list_append_deduplicate(PKG_CONFIG_LIBRARIES ${library})
  endforeach()
  alpine_unpack_libraries_with_build_configuration(PKG_CONFIG_LIBRARIES ${PKG_CONFIG_LIBRARIES})

  # .pc files can not handle build configuration keywords therefore filter them out based on the current build type
  set(PKG_CONFIG_LIBRARIES_WITH_PREFIX "")
  alpine_filter_libraries_for_build_configuration(libraries ${PKG_CONFIG_LIBRARIES})
  foreach(library ${libraries})
    if(IS_ABSOLUTE ${library})
      get_filename_component(suffix ${library} EXT)
      if(NOT "${suffix}" STREQUAL "${CMAKE_STATIC_LIBRARY_SUFFIX}")
        set(library "-l:${library}")
      endif()
    else()
      set(library "-l${library}")
    endif()
    list_append_deduplicate(PKG_CONFIG_LIBRARIES_WITH_PREFIX ${library})
  endforeach()

  #
  # DEVEL SPACE
  #

  # used in the cmake extra files
  set(DEVELSPACE TRUE)
  set(INSTALLSPACE FALSE)

  set(PROJECT_SPACE_DIR ${ALPINE_DEVEL_PREFIX})
  set(PKG_INCLUDE_PREFIX ${CMAKE_CURRENT_SOURCE_DIR})

  # absolute path to include dirs and validate that they are existing either absolute or relative to packages source
  set(PROJECT_CMAKE_CONFIG_INCLUDE_DIRS "")
  set(PROJECT_PKG_CONFIG_INCLUDE_DIRS "")
  foreach(idir ${PROJECT_INCLUDE_DIRS})
    if(IS_ABSOLUTE ${idir} AND IS_DIRECTORY ${idir})
      set(include ${idir})
    elseif(IS_DIRECTORY ${PKG_INCLUDE_PREFIX}/${idir})
      set(include ${PKG_INCLUDE_PREFIX}/${idir})
    else()
      message(FATAL_ERROR "alpine_project() include dir '${idir}' is neither an absolute directory nor exists relative to '${CMAKE_CURRENT_SOURCE_DIR}'")
    endif()
    list(APPEND PROJECT_CMAKE_CONFIG_INCLUDE_DIRS ${include})
    list(APPEND PROJECT_PKG_CONFIG_INCLUDE_DIRS ${include})
  endforeach()
  if(PROJECT_DEPENDENCIES_INCLUDE_DIRS)
    list(APPEND PROJECT_CMAKE_CONFIG_INCLUDE_DIRS ${PROJECT_DEPENDENCIES_INCLUDE_DIRS})
    list(APPEND PROJECT_PKG_CONFIG_INCLUDE_DIRS ${PROJECT_DEPENDENCIES_INCLUDE_DIRS})
  endif()

  # prepend library path of this workspace
  set(PKG_CONFIG_LIB_PATHS ${lib_paths})
  list(INSERT PKG_CONFIG_LIB_PATHS 0 ${PROJECT_SPACE_DIR}/lib)
  set(PKG_CMAKE_DIR ${PROJECT_SPACE_DIR}/share/${PROJECT_NAME}/cmake)
  if("${PROJECT_NAME}" STREQUAL "alpine")
    set(PKG_CMAKE_DIR "${alpine_EXTRAS_DIR}")
  endif()

  if(NOT PROJECT_SKIP_PKG_CONFIG_GENERATION)
    # ensure that output folder exists
    file(MAKE_DIRECTORY ${ALPINE_DEVEL_PREFIX}/lib/pkgconfig)
    # generate devel space pc for project
    em_expand(${alpine_EXTRAS_DIR}/templates/pkg.context.pc.in
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/pkg.develspace.context.pc.py
      ${alpine_EXTRAS_DIR}/em/pkg.pc.em
      ${ALPINE_DEVEL_PREFIX}/lib/pkgconfig/${PROJECT_NAME}.pc)
  endif()

  # generate devel space cfg-extras for project
  set(PKG_CFG_EXTRAS "")
  foreach(extra ${${PROJECT_NAME}_CFG_EXTRAS} ${PROJECT_CFG_EXTRAS})
    if(IS_ABSOLUTE ${extra})
      set(base ${extra})
      get_filename_component(extra ${extra} NAME)
    else()
      set(base ${CMAKE_CURRENT_SOURCE_DIR}/cmake/${extra})
    endif()
    if(EXISTS ${base}.em OR EXISTS ${base}.develspace.em)
      if(EXISTS ${base}.develspace.em)
        set(em_template ${base}.develspace.em)
      else()
        set(em_template ${base}.em)
      endif()
      em_expand(${alpine_EXTRAS_DIR}/templates/cfg-extras.context.py.in
        ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/${extra}.develspace.context.cmake.py
        ${em_template}
        ${ALPINE_DEVEL_PREFIX}/share/${PROJECT_NAME}/cmake/${extra})
      list(APPEND PKG_CFG_EXTRAS ${extra})
    elseif(EXISTS ${base}.in OR EXISTS ${base}.develspace.in)
      if(EXISTS ${base}.develspace.in)
        set(in_template ${base}.develspace.in)
      else()
        set(in_template ${base}.in)
      endif()
      configure_file(${in_template}
        ${ALPINE_DEVEL_PREFIX}/share/${PROJECT_NAME}/cmake/${extra}
        @ONLY
      )
      list(APPEND PKG_CFG_EXTRAS ${extra})
    elseif(EXISTS ${base})
      list(APPEND PKG_CFG_EXTRAS ${base})
    elseif(NOT EXISTS ${base}.installspace.em AND NOT EXISTS ${base}.installspace.in)
      message(FATAL_ERROR "alpine_project() could not find CFG_EXTRAS file.  Either 'cmake/${extra}.develspace.em', 'cmake/${extra}.em', 'cmake/${extra}.develspace.in', 'cmake/${extra}.in', 'cmake/${extra}' or a variant specific to the installspace must exist.")
    endif()
  endforeach()

  if(NOT PROJECT_SKIP_CMAKE_CONFIG_GENERATION)
    set(PKG_EXPORTED_TARGETS ${${PROJECT_NAME}_EXPORTED_TARGETS} ${PROJECT_EXPORTED_TARGETS})
    foreach(t ${PKG_EXPORTED_TARGETS})
      if(NOT TARGET ${t})
        message(FATAL_ERROR "alpine_project() could not find target '${t}' for code generation.")
      endif()
    endforeach()

    # generate devel space config for project
    set(infile ${${PROJECT_NAME}_EXTRAS_DIR}/${PROJECT_NAME}Config.cmake.in)
    if(NOT EXISTS ${infile})
      set(infile ${alpine_EXTRAS_DIR}/templates/pkgConfig.cmake.in)
    endif()
    configure_file(${infile}
      ${ALPINE_DEVEL_PREFIX}/share/${PROJECT_NAME}/cmake/${PROJECT_NAME}Config.cmake
      @ONLY
    )
    # generate devel space config-version for project
    configure_file(${alpine_EXTRAS_DIR}/templates/pkgConfig-version.cmake.in
      ${ALPINE_DEVEL_PREFIX}/share/${PROJECT_NAME}/cmake/${PROJECT_NAME}Config-version.cmake
      @ONLY
    )
  endif()

  #
  # INSTALLSPACE
  #

  # used in the cmake extra files
  set(DEVELSPACE FALSE)
  set(INSTALLSPACE TRUE)

  set(PROJECT_SPACE_DIR ${CMAKE_INSTALL_PREFIX})
  set(PKG_INCLUDE_PREFIX ${PROJECT_SPACE_DIR})

  # absolute path to include dir under install prefix if any include dir is set
  set(PROJECT_CMAKE_CONFIG_INCLUDE_DIRS "")
  set(PROJECT_PKG_CONFIG_INCLUDE_DIRS "")
  if(NOT "${PROJECT_INCLUDE_DIRS}" STREQUAL "")
    set(PROJECT_CMAKE_CONFIG_INCLUDE_DIRS "${ALPINE_GLOBAL_INCLUDE_DESTINATION}")
    set(PROJECT_PKG_CONFIG_INCLUDE_DIRS "${PKG_INCLUDE_PREFIX}/${ALPINE_GLOBAL_INCLUDE_DESTINATION}")
  endif()
  if(PROJECT_DEPENDENCIES_INCLUDE_DIRS)
    list(APPEND PROJECT_CMAKE_CONFIG_INCLUDE_DIRS ${PROJECT_DEPENDENCIES_INCLUDE_DIRS})
    list(APPEND PROJECT_PKG_CONFIG_INCLUDE_DIRS ${PROJECT_DEPENDENCIES_INCLUDE_DIRS})
  endif()

  # prepend library path of this workspace
  set(PKG_CONFIG_LIB_PATHS ${lib_paths})
  list(INSERT PKG_CONFIG_LIB_PATHS 0 ${PROJECT_SPACE_DIR}/lib)
  # package cmake dir is the folder where the generated pkgConfig.cmake is located
  set(PKG_CMAKE_DIR "\${${PROJECT_NAME}_DIR}")

  if(NOT PROJECT_SKIP_PKG_CONFIG_GENERATION)
    # ensure that output folder exists
    file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace)
    # generate and install pc for project
    em_expand(${alpine_EXTRAS_DIR}/templates/pkg.context.pc.in
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/pkg.installspace.context.pc.py
      ${alpine_EXTRAS_DIR}/em/pkg.pc.em
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${PROJECT_NAME}.pc)
    install(FILES ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${PROJECT_NAME}.pc
      DESTINATION lib/pkgconfig
    )
  endif()

  # generate and install cfg-extras for project
  set(PKG_CFG_EXTRAS "")
  set(installable_cfg_extras "")
  foreach(extra ${${PROJECT_NAME}_CFG_EXTRAS} ${PROJECT_CFG_EXTRAS})
    if(IS_ABSOLUTE ${extra})
      set(base ${extra})
      get_filename_component(extra ${extra} NAME)
    else()
      set(base ${CMAKE_CURRENT_SOURCE_DIR}/cmake/${extra})
    endif()
    if(EXISTS ${base}.em OR EXISTS ${base}.installspace.em)
      if(EXISTS ${base}.installspace.em)
        set(em_template ${base}.installspace.em)
      else()
        set(em_template ${base}.em)
      endif()
      em_expand(${alpine_EXTRAS_DIR}/templates/cfg-extras.context.py.in
        ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/${extra}.installspace.context.cmake.py
        ${em_template}
        ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${extra})
      list(APPEND installable_cfg_extras ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${extra})
      list(APPEND PKG_CFG_EXTRAS ${extra})
    elseif(EXISTS ${base}.in OR EXISTS ${base}.installspace.in)
      if(EXISTS ${base}.installspace.in)
        set(in_template ${base}.installspace.in)
      else()
        set(in_template ${base}.in)
      endif()
      configure_file(${in_template}
        ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${extra}
        @ONLY
      )
      list(APPEND installable_cfg_extras ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${extra})
      list(APPEND PKG_CFG_EXTRAS ${extra})
    elseif(EXISTS ${base})
      list(APPEND installable_cfg_extras ${base})
      list(APPEND PKG_CFG_EXTRAS ${extra})
    elseif(NOT EXISTS ${base}.develspace.em AND NOT EXISTS ${base}.develspace.in)
      message(FATAL_ERROR "alpine_project() could not find CFG_EXTRAS file.  Either 'cmake/${extra}.installspace.em', 'cmake/${extra}.em', 'cmake/${extra}.installspace.in', 'cmake/${extra}.in', 'cmake/${extra}'or a variant specific to the develspace must exist.")
    endif()
  endforeach()
  install(FILES
    ${installable_cfg_extras}
    DESTINATION share/${PROJECT_NAME}/cmake
  )

  if(NOT PROJECT_SKIP_CMAKE_CONFIG_GENERATION)
    # generate config for project
    set(infile ${${PROJECT_NAME}_EXTRAS_DIR}/${PROJECT_NAME}Config.cmake.in)
    if(NOT EXISTS ${infile})
      set(infile ${alpine_EXTRAS_DIR}/templates/pkgConfig.cmake.in)
    endif()
    configure_file(${infile}
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${PROJECT_NAME}Config.cmake
      @ONLY
    )
    # generate config-version for project
    set(infile ${${PROJECT_NAME}_EXTRAS_DIR}/${PROJECT_NAME}Config-version.cmake.in)
    if(NOT EXISTS ${infile})
      set(infile ${alpine_EXTRAS_DIR}/templates/pkgConfig-version.cmake.in)
    endif()
    configure_file(${infile}
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${PROJECT_NAME}Config-version.cmake
      @ONLY
    )
    # install config, config-version and cfg-extras for project
    install(FILES
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${PROJECT_NAME}Config.cmake
      ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/installspace/${PROJECT_NAME}Config-version.cmake
      DESTINATION share/${PROJECT_NAME}/cmake
    )
  endif()

  # install project.xml
  install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/project.xml
    DESTINATION share/${PROJECT_NAME}
  )
endfunction()
