cmake_minimum_required(VERSION 2.8.3)

set(alpine_EXTRAS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

project(alpine)

if(NOT DEFINED ALPINE_TOPLEVEL)
  	include(${alpine_EXTRAS_DIR}/all.cmake NO_POLICY_SCOPE)
endif()

alpine_project()


install(FILES DESTINATION ${ALPINE_PROJECT_SHARE_DESTINATION})


# install cmake files for alpine (except some files only used at build time of alpine)
install(DIRECTORY cmake
  	DESTINATION ${ALPINE_PROJECT_SHARE_DESTINATION}
  	USE_SOURCE_PERMISSIONS
  	PATTERN "alpineConfig.cmake.in" EXCLUDE
)

alpine_python_setup()

if(ALPINE_ENABLE_TESTING)
  	alpine_add_nosetests(test/local_tests)
  	alpine_add_nosetests(test/unit_tests)
endif()
