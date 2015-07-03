function(alpine_generate_environment)
  set(SETUP_FILENAME "setup")

  # devel space
  set(SETUP_DIR ${ALPINE_DEVEL_PREFIX})

  # generate empty file to prevent searching for packages in binary dir
  # except if source space and build space are identical (which is the case for dry eclipse projects)
  if(NOT "${CMAKE_BINARY_DIR}" STREQUAL "${CMAKE_CURRENT_SOURCE_DIR}")
    file(WRITE "${CMAKE_BINARY_DIR}/ALPINE_IGNORE" "")
  endif()

  # generate Python setup util
  atomic_configure_file(${alpine_EXTRAS_DIR}/templates/_setup_util.py.in
    ${ALPINE_DEVEL_PREFIX}/_setup_util.py
    @ONLY)

  if(NOT WIN32)
    # non-windows
    # generate env
    atomic_configure_file(${alpine_EXTRAS_DIR}/templates/env.sh.in
      ${ALPINE_DEVEL_PREFIX}/env.sh
      @ONLY)
    # generate setup for various shells
    foreach(shell bash sh zsh)
      atomic_configure_file(${alpine_EXTRAS_DIR}/templates/setup.${shell}.in
        ${ALPINE_DEVEL_PREFIX}/setup.${shell}
        @ONLY)
    endforeach()

  else()
    # windows
    # generate env
    atomic_configure_file(${alpine_EXTRAS_DIR}/templates/env.bat.in
      ${ALPINE_DEVEL_PREFIX}/env.bat
      @ONLY)
    # generate setup
    atomic_configure_file(${alpine_EXTRAS_DIR}/templates/setup.bat.in
      ${ALPINE_DEVEL_PREFIX}/setup.bat
      @ONLY)
  endif()

  # generate vminstall file referencing setup.sh
  atomic_configure_file(${alpine_EXTRAS_DIR}/templates/vminstall.in
    ${ALPINE_DEVEL_PREFIX}/.vminstall
    @ONLY)

  # installspace
  set(SETUP_DIR ${CMAKE_INSTALL_PREFIX})

  if(NOT ALPINE_BUILD_BINARY_PROJECT)
    # generate and install workspace marker
    file(WRITE ${CMAKE_BINARY_DIR}/alpine_generated/installspace/.alpine "")
    install(FILES
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/.alpine
      DESTINATION ${CMAKE_INSTALL_PREFIX})
    # generate and install Python setup util
    configure_file(${alpine_EXTRAS_DIR}/templates/_setup_util.py.in
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/_setup_util.py
      @ONLY)
    alpine_install_python(PROGRAMS
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/_setup_util.py
      DESTINATION ${CMAKE_INSTALL_PREFIX})
  endif()

  if(NOT WIN32)
    # non-windows
    # generate and install env
    configure_file(${alpine_EXTRAS_DIR}/templates/env.sh.in
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/env.sh
      @ONLY)
    if(NOT ALPINE_BUILD_BINARY_PROJECT)
      install(PROGRAMS
        ${CMAKE_BINARY_DIR}/alpine_generated/installspace/env.sh
        DESTINATION ${CMAKE_INSTALL_PREFIX})
    endif()
    # generate and install setup for various shells
    foreach(shell bash sh zsh)
      configure_file(${alpine_EXTRAS_DIR}/templates/setup.${shell}.in
        ${CMAKE_BINARY_DIR}/alpine_generated/installspace/setup.${shell}
        @ONLY)
      if(NOT ALPINE_BUILD_BINARY_PROJECT)
        install(FILES
          ${CMAKE_BINARY_DIR}/alpine_generated/installspace/setup.${shell}
          DESTINATION ${CMAKE_INSTALL_PREFIX})
      endif()
    endforeach()

  else()
    # windows
    # generate and install env
    configure_file(${alpine_EXTRAS_DIR}/templates/env.bat.in
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/env.bat
      @ONLY)
    install(PROGRAMS
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/env.bat
      DESTINATION ${CMAKE_INSTALL_PREFIX})
    # generate and install setup
    configure_file(${alpine_EXTRAS_DIR}/templates/setup.bat.in
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/setup.bat
      @ONLY)
    install(FILES
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/setup.bat
      DESTINATION ${CMAKE_INSTALL_PREFIX})
  endif()

  # generate vminstall file referencing setup.sh
  configure_file(${alpine_EXTRAS_DIR}/templates/vminstall.in
    ${CMAKE_BINARY_DIR}/alpine_generated/installspace/.vminstall
    @ONLY)
  if(NOT ALPINE_BUILD_BINARY_PROJECT)
    install(FILES
      ${CMAKE_BINARY_DIR}/alpine_generated/installspace/.vminstall
      DESTINATION ${CMAKE_INSTALL_PREFIX})
  endif()
endfunction()
