#
# Insert elements to a list in the same order as the chained alpine workspaces.
#
set(ALPINE_ORDERED_SPACES "")
foreach(_space ${ALPINE_DEVEL_PREFIX} ${ALPINE_WORKSPACES})
  list(APPEND ALPINE_ORDERED_SPACES ${_space})
  if(NOT EXISTS "${_space}/.alpine")
    message(FATAL_ERROR "The path '${_space}' is in ALPINE_WORKSPACES but does not have a .alpine file")
  endif()
  # prepend to existing list of sourcespaces
  file(READ "${_space}/.alpine" _sourcespaces)
  list(APPEND ALPINE_ORDERED_SPACES ${_sourcespaces})
endforeach()

debug_message(10 "ALPINE_ORDERED_SPACES ${ALPINE_ORDERED_SPACES}")

macro(list_insert_in_workspace_order listname)
  if(NOT "${ARGN}" STREQUAL "")
    assert(ALPINE_ENV)
    assert(PYTHON_EXECUTABLE)
    set(cmd
      ${ALPINE_ENV} ${PYTHON_EXECUTABLE}
      ${alpine_EXTRAS_DIR}/order_paths.py
      ${${PROJECT_NAME}_BINARY_DIR}/alpine_generated/ordered_paths.cmake
      --paths-to-order ${ARGN}
      --prefixes ${ALPINE_ORDERED_SPACES}
    )
    debug_message(10 "list_insert_in_workspace_order() in project '{PROJECT_NAME}' executes:  ${cmd}")
    safe_execute_process(COMMAND ${cmd})
    include(${${PROJECT_NAME}_BINARY_DIR}/alpine_generated/ordered_paths.cmake)
    set(${listname} ${ORDERED_PATHS})
  else()
    set(${listname} "")
  endif()
endmacro()
