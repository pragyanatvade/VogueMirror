# message("CMAKE_LIBRARY_PATH: ${CMAKE_LIBRARY_PATH}")
# message("CMAKE_LIBRARY_ARCHITECTURE: ${CMAKE_LIBRARY_ARCHITECTURE}")
# message("CMAKE_SYSTEM_LIBRARY_PATH: ${CMAKE_SYSTEM_LIBRARY_PATH}")
# message("CMAKE_VERSION=${CMAKE_VERSION}")

if(NOT (APPLE OR WIN32 OR MINGW OR ANDROID))
  if (${CMAKE_VERSION} VERSION_LESS 2.8.4)
    # cmake later than 2.8.0 appears to have a better find_library
    # that knows about the ABI of the compiler.  For lucid we just
    # depend on the linker to find it for us.
    set(RT_LIBRARY rt CACHE FILEPATH "Hacked find of rt for cmake < 2.8.4")
  else()
    find_library(RT_LIBRARY rt)
    assert_file_exists(${RT_LIBRARY} "RT Library")
  endif()
  #message(STATUS "RT_LIBRARY: ${RT_LIBRARY}")
endif()
