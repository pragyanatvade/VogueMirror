#
# Search all subfolders in the workspace for ``project.xml`` files.
# Based on the dependencies specified in the ``builddeps`` and
# ``buildtooldeps`` tags it performs a topological sort and calls
# ``add_subdirectory()`` for each directory.
#
# The functions is only called in alpine's ``toplevel.cmake``, which
# is usually symlinked to the workspace root directory (which
# contains multiple packages).
#
function(alpine_workspace)
  debug_message(10 "alpine_workspace() called in file '${CMAKE_CURRENT_LIST_FILE}'")

  # set global output directories for artifacts and create them if necessary
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${ALPINE_DEVEL_PREFIX}/lib)
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${ALPINE_DEVEL_PREFIX}/lib)
  if(NOT IS_DIRECTORY ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    file(MAKE_DIRECTORY ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
  endif()

  # tools/libraries.cmake
  configure_shared_library_build_settings()

  set(ALPINE_WHITELIST_PROJECTS "" CACHE STRING "List of ';' separated projects to build")
  set(ALPINE_BLACKLIST_PROJECTS "" CACHE STRING "List of ';' separated projects to exclude")

  assert(alpine_EXTRAS_DIR)
  em_expand(
    ${alpine_EXTRAS_DIR}/templates/order_projects.context.py.in
    ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/order_projects.py
    ${alpine_EXTRAS_DIR}/em/order_projects.cmake.em
    ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/order_projects.cmake
    )
  debug_message(10 "alpine_workspace() including order_projects.cmake")
  include(${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/order_projects.cmake)

  if(ALPINE_ORDERED_PROJECTS)
    set(ALPINE_NONCONFORMANT_METAPROJECT FALSE)
    set(ALPINE_NONHOMOGENEOUS_WORKSPACE FALSE)
    list(LENGTH ALPINE_ORDERED_PROJECTS count)
    message(STATUS "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    message(STATUS "~~  traversing ${count} project in topological order:")
    math(EXPR range "${count} - 1")
    foreach(index RANGE ${range})
      list(GET ALPINE_ORDERED_PROJECTS ${index} name)
      list(GET ALPINE_ORDERED_PROJECT_PATHS ${index} path)
      list(GET ALPINE_ORDERED_PROJECTS_IS_META ${index} is_meta)
      list(GET ALPINE_ORDERED_PROJECTS_BUILD_TYPE ${index} build_type)
      if(${is_meta})
        message(STATUS "~~  - ${name} (metaproject)")
        # verify that CMakeLists.txt of metaproject conforms to standard
        set(metaproject_arguments "")
        assert(ALPINE_METAPROJECT_CMAKE_TEMPLATE)
        configure_file(${ALPINE_METAPROJECT_CMAKE_TEMPLATE}
          ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/metaprojects/${name}/CMakeLists.txt
          @ONLY)
        if(EXISTS ${CMAKE_SOURCE_DIR}/${path}/CMakeLists.txt)
          # compare CMakeLists.txt with standard content
          file(STRINGS ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/metaprojects/${name}/CMakeLists.txt generated_cmakelists)
          file(STRINGS ${path}/CMakeLists.txt existing_cmakelists)
          if(NOT "${generated_cmakelists}" STREQUAL "${existing_cmakelists}")
            set(ALPINE_NONHOMOGENEOUS_WORKSPACE TRUE)
            message("WARNING: The CMakeLists.txt of the metaproject '${name}' contains non standard content. Use the content of the following file instead: ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/metaprojects/${name}/CMakeLists.txt")
          endif()
        else()
          message("WARNING: The metaproject '${name}' has no CMakeLists.txt. Please add one to the project source. You can use the following file: ${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/metaprojects/${name}/CMakeLists.txt")
        endif()
      else()
        if(${build_type} MATCHES alpine)
          message(STATUS "~~  - ${name}")
        else()
          set(ALPINE_NONHOMOGENEOUS_WORKSPACE TRUE)
          if(${build_type} MATCHES cmake)
            message(STATUS "~~  - ${name} (plain cmake)")
          else()
            message(STATUS "~~  - ${name} (unknown)")
            message(WARNING "Unknown build type '${build_type}' for project '${name}'")
          endif()
        endif()
      endif()
    endforeach()
    message(STATUS "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    if(${ALPINE_NONCONFORMANT_METAPROJECT})
      message(FATAL_ERROR "This workspace contains metaprojects with a non-standard CMakeLists.txt.")
    endif()
    if(${ALPINE_NONHOMOGENEOUS_WORKSPACE})
      message(FATAL_ERROR "This workspace contains non-alpine projects in it, and alpine cannot build a non-homogeneous workspace without isolation.")
    endif()

    foreach(index RANGE ${range})
      list(GET ALPINE_ORDERED_PROJECTS ${index} name)
      list(GET ALPINE_ORDERED_PROJECT_PATHS ${index} path)
      list(GET ALPINE_ORDERED_PROJECTS_IS_META ${index} is_meta)
      list(GET ALPINE_ORDERED_PROJECTS_BUILD_TYPE ${index} build_type)
      if(${is_meta})
        message(STATUS "+++ processing alpine metaproject: '${name}'")
        if(EXISTS ${CMAKE_SOURCE_DIR}/${path}/CMakeLists.txt)
          message(STATUS "==> add_subdirectory(${path})")
          add_subdirectory(${path})
        else()
          message(STATUS "==> add_subdirectory(${path}) (using generated file from <buildspace>/alpine_generated/metaprojects/${name})")
          message("WARNING: Add a CMakeLists.txt file to the metaproject '${name}'")
          add_subdirectory(${CMAKE_CURRENT_BINARY_DIR}/alpine_generated/metaprojects/${name} ${CMAKE_BINARY_DIR}/${path})
        endif()
      elseif(${build_type} MATCHES alpine)
        message(STATUS "+++ processing alpine project: '${name}'")
        message(STATUS "==> add_subdirectory(${path})")
        add_subdirectory(${path})
      else()
        message(FATAL_ERROR "Non-alpine project found, non-homogeneous workspaces are not supported.")
      endif()
    endforeach()
  endif()
endfunction()
