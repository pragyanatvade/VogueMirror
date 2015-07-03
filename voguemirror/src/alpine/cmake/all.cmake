# prevent multiple inclusion
if(DEFINED _ALPINE_ALL_INCLUDED_)
    message(FATAL_ERROR "alpine/cmake/all.cmake included multiple times")
endif()
set(_ALPINE_ALL_INCLUDED_ TRUE)

if(NOT DEFINED alpine_EXTRAS_DIR)
    message(FATAL_ERROR "alpine_EXTRAS_DIR is not set")
endif()

# define devel space
if(ALPINE_DEVEL_PREFIX)
    set(ALPINE_DEVEL_PREFIX ${ALPINE_DEVEL_PREFIX} CACHE PATH "alpine devel space")
else()
    set(ALPINE_DEVEL_PREFIX "${CMAKE_BINARY_DIR}/devel")
endif()
message(STATUS "Using ALPINE_DEVEL_PREFIX: ${ALPINE_DEVEL_PREFIX}")

# create workspace marker
set(_sourcespaces "${CMAKE_SOURCE_DIR}")
if(EXISTS "${ALPINE_DEVEL_PREFIX}/.alpine")
    # prepend to existing list of sourcespaces
    file(READ "${ALPINE_DEVEL_PREFIX}/.alpine" _existing_sourcespaces)
    list(FIND _existing_sourcespaces "${CMAKE_SOURCE_DIR}" _index)
    if(_index EQUAL -1)
        list(INSERT _existing_sourcespaces 0 ${CMAKE_SOURCE_DIR})
    endif()
    set(_sourcespaces ${_existing_sourcespaces})
endif()
file(WRITE "${ALPINE_DEVEL_PREFIX}/.alpine" "${_sourcespaces}")


# use either CMAKE_PREFIX_PATH explicitly passed to CMake as a command line argument
# or CMAKE_PREFIX_PATH from the environment
if(NOT DEFINED CMAKE_PREFIX_PATH)
    if(NOT "$ENV{CMAKE_PREFIX_PATH}" STREQUAL "")
        string(REPLACE ":" ";" CMAKE_PREFIX_PATH $ENV{CMAKE_PREFIX_PATH})
    endif()
endif()
message(STATUS "Using CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")
# store original CMAKE_PREFIX_PATH
set(CMAKE_PREFIX_PATH_AS_IS ${CMAKE_PREFIX_PATH})

# list of unique alpine workspaces based on CMAKE_PREFIX_PATH
set(ALPINE_WORKSPACES "")
foreach(path ${CMAKE_PREFIX_PATH})
    if(EXISTS "${path}/.alpine")
        list(FIND ALPINE_WORKSPACES ${path} _index)
        if(_index EQUAL -1)
            list(APPEND ALPINE_WORKSPACES ${path})
        endif()
    endif()
endforeach()
if(ALPINE_WORKSPACES)
    message(STATUS "This workspace overlays: ${ALPINE_WORKSPACES}")
endif()

# prepend devel space to CMAKE_PREFIX_PATH
list(FIND CMAKE_PREFIX_PATH ${ALPINE_DEVEL_PREFIX} _index)
if(_index EQUAL -1)
    list(INSERT CMAKE_PREFIX_PATH 0 ${ALPINE_DEVEL_PREFIX})
endif()


# enable all new policies (if available)
macro(_set_cmake_policy_to_new_if_available policy)
    if(POLICY ${policy})
        cmake_policy(SET ${policy} NEW)
    endif()
endmacro()
_set_cmake_policy_to_new_if_available(CMP0000)
_set_cmake_policy_to_new_if_available(CMP0001)
_set_cmake_policy_to_new_if_available(CMP0002)
_set_cmake_policy_to_new_if_available(CMP0003)
_set_cmake_policy_to_new_if_available(CMP0004)
_set_cmake_policy_to_new_if_available(CMP0005)
_set_cmake_policy_to_new_if_available(CMP0006)
_set_cmake_policy_to_new_if_available(CMP0007)
_set_cmake_policy_to_new_if_available(CMP0008)
_set_cmake_policy_to_new_if_available(CMP0009)
_set_cmake_policy_to_new_if_available(CMP0010)
_set_cmake_policy_to_new_if_available(CMP0011)
_set_cmake_policy_to_new_if_available(CMP0012)
_set_cmake_policy_to_new_if_available(CMP0013)
_set_cmake_policy_to_new_if_available(CMP0014)
_set_cmake_policy_to_new_if_available(CMP0015)
_set_cmake_policy_to_new_if_available(CMP0016)
_set_cmake_policy_to_new_if_available(CMP0017)

# the following operations must be performed inside a project context
if(NOT PROJECT_NAME)
    project(alpine_internal)
endif()

# include CMake functions
include(CMakeParseArguments)

# functions/macros: list_append_unique, safe_execute_process
# python-integration: alpine_python_setup.cmake, interrogate_setup_dot_py.py, templates/__init__.py.in, templates/script.py.in, templates/python_distutils_install.bat.in, templates/python_distutils_install.sh.in, templates/safe_execute_install.cmake.in
foreach(filename
    assert
    atomic_configure_file
    alpine_add_env_hooks
    alpine_destinations
    alpine_generate_environment
    alpine_install_python
    alpine_libraries
    alpine_metaproject
    alpine_project
    alpine_project_xml
    alpine_workspace
    debug_message
    em_expand
    python # defines PYTHON_EXECUTABLE, required by empy
    empy
    find_program_required
    list_append_deduplicate
    list_append_unique
    list_insert_in_workspace_order
    safe_execute_process
    stamp
    test/tests # defines ALPINE_ENABLE_TESTING, required by other test functions
    test/alpine_download_test_data
    test/gtest
    test/nosetests
    tools/doxygen
    tools/libraries
    tools/rt
)
    include(${alpine_EXTRAS_DIR}/${filename}.cmake)
endforeach()

# output alpine version for debugging
_alpine_project_xml(${CMAKE_BINARY_DIR}/alpine/alpine_generated/version DIRECTORY ${alpine_EXTRAS_DIR}/..)
message(STATUS "alpine ${alpine_VERSION}")
# ensure that no current project name is set
unset(_ALPINE_CURRENT_PROJECT)

# set global install destinations
set(ALPINE_GLOBAL_BIN_DESTINATION bin)
set(ALPINE_GLOBAL_ETC_DESTINATION etc)
set(ALPINE_GLOBAL_INCLUDE_DESTINATION include)
set(ALPINE_GLOBAL_LIB_DESTINATION lib)
set(ALPINE_GLOBAL_LIBEXEC_DESTINATION lib)
set(ALPINE_GLOBAL_PYTHON_DESTINATION ${PYTHON_INSTALL_DIR})
set(ALPINE_GLOBAL_SHARE_DESTINATION share)

# undefine ALPINE_ENV since it might be set in the cache from a previous build
set(ALPINE_ENV "" CACHE INTERNAL "alpine environment" FORCE)

# generate environment files like env.* and setup.*
# uses em_expand without ALPINE_ENV being set yet
alpine_generate_environment()

# file extension of env script
if(CMAKE_HOST_UNIX) # true for linux, apple, mingw-cross and cygwin
    set(script_ext sh)
else()
    set(script_ext bat)
endif()
# take snapshot of the modifications the setup script causes
# to reproduce the same changes with a static script in a fraction of the time
set(SETUP_DIR ${CMAKE_BINARY_DIR}/alpine_generated)
set(SETUP_FILENAME "setup_cached")
configure_file(${alpine_EXTRAS_DIR}/templates/generate_cached_setup.py.in
    ${CMAKE_BINARY_DIR}/alpine_generated/generate_cached_setup.py)
set(GENERATE_ENVIRONMENT_CACHE_COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_BINARY_DIR}/alpine_generated/generate_cached_setup.py)
# the script is generated once here and refreshed by every call to alpine_add_env_hooks()
safe_execute_process(COMMAND ${GENERATE_ENVIRONMENT_CACHE_COMMAND})
# generate env_cached which just relays to the setup_cached
configure_file(${alpine_EXTRAS_DIR}/templates/env.${script_ext}.in
    ${SETUP_DIR}/env_cached.${script_ext}
    @ONLY)
# environment to call external processes
set(ALPINE_ENV ${SETUP_DIR}/env_cached.${script_ext} CACHE INTERNAL "alpine environment")

# add additional environment hooks
if(ALPINE_BUILD_BINARY_PROJECT)
    set(alpine_skip_install_env_hooks "SKIP_INSTALL")
endif()
if(CMAKE_HOST_UNIX)
    alpine_add_env_hooks(05.alpine_make SHELLS bash DIRECTORY ${alpine_EXTRAS_DIR}/env-hooks ${alpine_skip_install_env_hooks})
    alpine_add_env_hooks(05.alpine_make_isolated SHELLS bash DIRECTORY ${alpine_EXTRAS_DIR}/env-hooks ${alpine_skip_install_env_hooks})
    alpine_add_env_hooks(05.alpine-test-results SHELLS sh DIRECTORY ${alpine_EXTRAS_DIR}/env-hooks ${alpine_skip_install_env_hooks})
else()
    alpine_add_env_hooks(05.alpine-test-results SHELLS bat DIRECTORY ${alpine_EXTRAS_DIR}/env-hooks ${alpine_skip_install_env_hooks})
endif()

# requires stamp and environment files
include(${alpine_EXTRAS_DIR}/alpine_python_setup.cmake)
