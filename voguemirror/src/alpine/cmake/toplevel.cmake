# toplevel CMakeLists.txt for a alpine workspace
# alpine/cmake/toplevel.cmake

cmake_minimum_required(VERSION 2.8.3)

set(ALPINE_TOPLEVEL TRUE)

# search for alpine within the workspace
set(_cmd "alpine_find_project" "alpine" "${CMAKE_SOURCE_DIR}")
execute_process(COMMAND ${_cmd}
  RESULT_VARIABLE _res
  OUTPUT_VARIABLE _out
  ERROR_VARIABLE _err
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_STRIP_TRAILING_WHITESPACE
)
if(NOT _res EQUAL 0 AND NOT _res EQUAL 2)
  # searching fot alpine resulted in an error
  string(REPLACE ";" " " _cmd_str "${_cmd}")
  message(FATAL_ERROR "Search for 'alpine' in workspace failed (${_cmd_str}): ${_err}")
endif()

# include alpine from workspace or via find_package()
if(_res EQUAL 0)
  set(alpine_EXTRAS_DIR "${CMAKE_SOURCE_DIR}/${_out}/cmake")
  # include all.cmake without add_subdirectory to let it operate in same scope
  include(${alpine_EXTRAS_DIR}/all.cmake NO_POLICY_SCOPE)
  add_subdirectory("${_out}")

else()
  # use either CMAKE_PREFIX_PATH explicitly passed to CMake as a command line argument
  # or CMAKE_PREFIX_PATH from the environment
  if(NOT DEFINED CMAKE_PREFIX_PATH)
    if(NOT "$ENV{CMAKE_PREFIX_PATH}" STREQUAL "")
      string(REPLACE ":" ";" CMAKE_PREFIX_PATH $ENV{CMAKE_PREFIX_PATH})
    endif()
  endif()

  # list of alpine workspaces
  set(alpine_search_path "")
  foreach(path ${CMAKE_PREFIX_PATH})
    if(EXISTS "${path}/.alpine")
      list(FIND alpine_search_path ${path} _index)
      if(_index EQUAL -1)
        list(APPEND alpine_search_path ${path})
      endif()
    endif()
  endforeach()

  # search for alpine in all workspaces
  set(ALPINE_TOPLEVEL_FIND_PROJECT TRUE)
  find_package(alpine QUIET
    NO_POLICY_SCOPE
    PATHS ${alpine_search_path}
    NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
  unset(ALPINE_TOPLEVEL_FIND_PROJECT)

  if(NOT alpine_FOUND)
    message(FATAL_ERROR "find_package(alpine) failed. alpine was neither found in the workspace nor in the CMAKE_PREFIX_PATH. One reason may be that no ROS setup.sh was sourced before.")
  endif()
endif()

alpine_workspace()
