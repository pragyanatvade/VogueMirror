_generate_function_if_testing_is_disabled("alpine_add_gtest")

#
# Add a GTest based test target.
#
# An executable target is created with the source files, it is linked
# against GTest and added to the set of unit tests.
#
# .. note:: The test can be executed by calling the binary directly
#   or using: ``make run_tests_${PROJECT_NAME}_gtest_${target}``
#
# :param target: the target name
# :type target: string
# :param source_files: a list of source files used to build the test
#   executable
# :type source_files: list of strings
# :param TIMEOUT: currently not supported
# :type TIMEOUT: integer
# :param WORKING_DIRECTORY: the working directory when executing the
#   executable
# :type WORKING_DIRECTORY: string
#
# @public
#
function(alpine_add_gtest target)
  find_package(Threads)
  _warn_if_skip_testing("alpine_add_gtest")

  if(NOT GTEST_FOUND AND NOT GTEST_FROM_SOURCE_FOUND)
    message(WARNING "skipping gtest '${target}' in project '${PROJECT_NAME}'")
    return()
  endif()

  if(NOT DEFINED CMAKE_RUNTIME_OUTPUT_DIRECTORY)
    message(FATAL_ERROR "alpine_add_gtest() must be called after alpine_project() so that default output directories for the test binaries are defined")
  endif()

  # XXX look for optional TIMEOUT argument, #2645
  cmake_parse_arguments(_gtest "" "TIMEOUT;WORKING_DIRECTORY" "" ${ARGN})
  if(_gtest_TIMEOUT)
    message(WARNING "TIMEOUT argument to alpine_add_gtest() is ignored")
  endif()

  # create the executable, with basic + gtest build flags
  include_directories(${GTEST_INCLUDE_DIRS})
  link_directories(${GTEST_LIBRARY_DIRS})
  add_executable(${target} EXCLUDE_FROM_ALL ${_gtest_UNPARSED_ARGUMENTS})
  assert(GTEST_LIBRARIES)
  target_link_libraries(${target} ${GTEST_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT})

  # make sure gtest is built before the test target
  add_dependencies(${target} gtest gtest_main)
  # make sure the target is built before running tests
  add_dependencies(tests ${target})

  # XXX we DONT use rosunit to call the executable to get process control, #1629, #3112
  get_target_property(_target_path ${target} RUNTIME_OUTPUT_DIRECTORY)
  set(cmd "${_target_path}/${target} --gtest_output=xml:${ALPINE_TEST_RESULTS_DIR}/${PROJECT_NAME}/gtest-${target}.xml")
  alpine_run_tests_target("gtest" ${target} "gtest-${target}.xml" COMMAND ${cmd} DEPENDENCIES ${target} WORKING_DIRECTORY ${_gtest_WORKING_DIRECTORY})
endfunction()

find_package(GTest QUIET)
if(NOT GTEST_FOUND)
  # only add gtest directory once per workspace
  if(NOT TARGET gtest)
    find_file(_ALPINE_GTEST_SRC "gtest.cc"
      PATHS
      # search in the current workspace
      "${CMAKE_SOURCE_DIR}/gtest/src"
      # fall back to system installed path (i.e. on Ubuntu)
      "/usr/src/gtest/src"
      NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
    find_file(_ALPINE_GTEST_INCLUDE "gtest/gtest.h"
      PATHS
      # search in the current workspace
      "${CMAKE_SOURCE_DIR}/gtest/include"
      # fall back to system installed path (i.e. on Ubuntu)
      "/usr/include/gtest"
      NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)

    if(_ALPINE_GTEST_SRC)
      get_filename_component(_ALPINE_GTEST_SOURCE_DIR ${_ALPINE_GTEST_SRC} PATH)
      get_filename_component(_ALPINE_GTEST_BASE_DIR ${_ALPINE_GTEST_SOURCE_DIR} PATH)
      # add CMakeLists.txt from gtest dir
      set(_ALPINE_GTEST_BINARY_DIR ${CMAKE_BINARY_DIR}/gtest)
      add_subdirectory(${_ALPINE_GTEST_BASE_DIR} ${_ALPINE_GTEST_BINARY_DIR})
      # mark gtest targets with EXCLUDE_FROM_ALL to only build when tests are built which depend on them
      set_target_properties(gtest gtest_main PROPERTIES EXCLUDE_FROM_ALL 1)
      get_filename_component(_ALPINE_GTEST_INCLUDE_DIR ${_ALPINE_GTEST_INCLUDE} PATH)
      # set from-source variables
      set(GTEST_FROM_SOURCE_FOUND TRUE CACHE INTERNAL "")
      set(GTEST_FROM_SOURCE_INCLUDE_DIRS ${_ALPINE_GTEST_INCLUDE_DIR} CACHE INTERNAL "")
      set(GTEST_FROM_SOURCE_LIBRARY_DIRS ${_ALPINE_GTEST_BINARY_DIR} CACHE INTERNAL "")
      set(GTEST_FROM_SOURCE_LIBRARIES "gtest" CACHE INTERNAL "")
      set(GTEST_FROM_SOURCE_MAIN_LIBRARIES "gtest_main" CACHE INTERNAL "")
      message(STATUS "Found gtest sources under '${_ALPINE_GTEST_BASE_DIR}': gtests will be built")
    endif()
    if(NOT GTEST_FROM_SOURCE_FOUND)
      message(STATUS "gtest not found, C++ tests can not be built. You can run 'svn checkout http://googletest.googlecode.com/svn/tags/release-1.6.0 gtest' in the source space '${CMAKE_SOURCE_DIR}' of your workspace")
    endif()
  endif()
  if(GTEST_FROM_SOURCE_FOUND)
    # set the same variables as find_package()
    # do NOT set GTEST_FOUND in the cache since when using gtest from source
    # we must always add the subdirectory to have the gtest targets defined
    set(GTEST_FOUND ${GTEST_FROM_SOURCE_FOUND})
    set(GTEST_INCLUDE_DIRS ${GTEST_FROM_SOURCE_INCLUDE_DIRS})
    set(GTEST_LIBRARY_DIRS ${GTEST_FROM_SOURCE_LIBRARY_DIRS})
    set(GTEST_LIBRARIES ${GTEST_FROM_SOURCE_LIBRARIES})
    set(GTEST_MAIN_LIBRARIES ${GTEST_FROM_SOURCE_MAIN_LIBRARIES})
    set(GTEST_BOTH_LIBRARIES ${GTEST_LIBRARIES} ${GTEST_MAIN_LIBRARIES})
  endif()
else()
  message(STATUS "Found gtest: gtests will be built")
  set(GTEST_FOUND ${GTEST_FOUND} CACHE INTERNAL "")
  set(GTEST_INCLUDE_DIRS ${GTEST_INCLUDE_DIRS} CACHE INTERNAL "")
  set(GTEST_LIBRARIES ${GTEST_LIBRARIES} CACHE INTERNAL "")
  set(GTEST_MAIN_LIBRARIES ${GTEST_MAIN_LIBRARIES} CACHE INTERNAL "")
  set(GTEST_BOTH_LIBRARIES ${GTEST_BOTH_LIBRARIES} CACHE INTERNAL "")
endif()
# For Visual C++, need to increase variadic template size to build gtest
if(GTEST_FOUND)
  if(WIN32) 
    add_definitions(/D _VARIADIC_MAX=10)
  endif()
endif()