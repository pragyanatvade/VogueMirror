cmake_minimum_required(VERSION 2.8.3)
project(cmake_modules)

find_package(alpine REQUIRED)

alpine_project(
	CFG_EXTRAS cmake_modules-extras.cmake
)

install(DIRECTORY cmake/Modules
	DESTINATION ${ALPINE_PROJECT_SHARE_DESTINATION}/cmake)