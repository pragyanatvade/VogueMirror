# Log levels
# 0 Normal use
# 1 Alpine developer use (Stuff being developed)
# 2 Alpine developer use (Stuff working)
# 3 Also Print True Assert Statements

macro(debug_message level)
  set(loglevel ${ALPINE_LOG})
  if(NOT loglevel)
    set(loglevel 0)
  endif()

  if(NOT ${level} GREATER ${loglevel})
    message(STATUS "  ${ARGN}")
  endif()
endmacro()
