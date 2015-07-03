# doxygen(<TARGET_NAME> <SEARCH_DIRS>)
# TARGET_NAME -> The cmake target to create.
# SEARCH_DIRS -> a CMake List of directories to search for doxygenated files.
#
find_program(DOXYGEN_EXECUTABLE doxygen)

if (DOXYGEN_EXECUTABLE)
  set(DOXYGEN_FOUND TRUE CACHE BOOL "Doxygen found")
endif()

GET_TARGET_PROPERTY(doxygen_alpine_property doxygen "alpine")
if (doxygen_alpine_property)
else()
  add_custom_target(doxygen COMMENT "doxygen found")
  set_target_properties(doxygen PROPERTIES "alpine" "found")
endif()

macro(alpine_doxygen TARGET_NAME SEARCH_DIRS)
  foreach(dir ${SEARCH_DIRS})
    file(GLOB_RECURSE _doc_sources ${dir}/*)
    list(APPEND doc_sources ${_doc_sources})
  endforeach()

  string(REPLACE ";" " " doc_sources "${doc_sources}")

  configure_file(${alpine_EXTRAS_DIR}/templates/Doxyfile.in ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile @ONLY)

  add_custom_target(${TARGET_NAME}
    COMMENT "Generating API documentation with Doxygen" VERBATIM
    )

  add_custom_command(TARGET ${TARGET_NAME}
    COMMAND ${DOXYGEN_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    )
  add_dependencies(doxygen ${TARGET_NAME})

endmacro()
