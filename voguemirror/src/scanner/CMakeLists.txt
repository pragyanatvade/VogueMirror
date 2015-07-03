cmake_minimum_required(VERSION 2.8.7)

set(CMAKE_CONFIGURATION_TYPES "Debug;Release" CACHE STRING "Possible configurations" FORCE)
if (DEFINED CMAKE_BUILD_TYPE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS ${CMAKE_CONFIGURATION_TYPES})
endif()

project(scanner)

find_package(alpine REQUIRED COMPONENTS cmake_modules)
find_package(OpenNI REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core viz highgui imgproc)
find_package(CUDA REQUIRED)

alpine_project(
	INCLUDE_DIRS include
	LIBRARIES scanner
	DEPENDS openni opencv cuda
)

###########
## Build ##
###########

include_directories(
	include
	${alpine_INCLUDE_DIRS}
	${OPENNI_INCLUDE_DIRS}
	${OpenCV_INCLUDE_DIRS}
	${CUDA_INCLUDE_DIRS}
)

# ---[ cuda settings
if(CUDA_FOUND)
  message(STATUS "Found CUDA Toolkit v${CUDA_VERSION_STRING}")

  # CUDA_ARCH_BIN is a space separated list of versions to include in output so-file. So you can set CUDA_ARCH_BIN = 10 11 12 13 20
  # Also user can specify virtual arch in parenthesis to limit instructions  set, 
  # for example CUDA_ARCH_BIN = 11(11) 12(11) 13(11) 20(11) 21(11) -> forces using only sm_11 instructions.
  # The CMake scripts interpret XX as XX (XX). This allows user to omit parenthesis. 
  # Arch 21 is an exceptional case since it doesn't have own sm_21 instructions set. 
  # So 21 = 21(21) is an invalid configuration and user has to explicitly force previous sm_20 instruction set via 21(20).
  # CUDA_ARCH_BIN adds support of only listed GPUs. As alternative CMake scripts also parse 'CUDA_ARCH_PTX' variable,
  # which is a list of intermediate PTX codes to include in final so-file. The PTX code can/will be JIT compiled for any current or future GPU. 
  # To add support of older GPU for kinfu, I would embed PTX 11 and 12 into so-file. GPU with sm_13  will run PTX 12 code (no difference for kinfu)
  
  # Find a complete list for CUDA compute capabilities at http://developer.nvidia.com/cuda-gpus

  if(${CUDA_VERSION_STRING} VERSION_GREATER "4.1")
    set(CUDA_ARCH_BIN "2.0 2.1(2.0) 3.0" CACHE STRING "Specify 'real' GPU architectures to build binaries for, BIN(PTX) format is supported")
  else()
    set(CUDA_ARCH_BIN "2.0 2.1(2.0)" CACHE STRING "Specify 'real' GPU architectures to build binaries for, BIN(PTX) format is supported")
  endif()

  set(CUDA_ARCH_PTX "" CACHE STRING "Specify 'virtual' PTX arch to build PTX intermediate code for. Example: 1.0 1.2 or 10 12")
  #set(CUDA_ARCH_PTX "1.1 1.2" CACHE STRING "Specify 'virtual' PTX arch to build PTX intermediate code for. Example: 1.0 1.2 or 10 12")

  # Send a warning if CUDA_HOST_COMPILER is set to a compiler that is known
  # to be unsupported.
  if (CUDA_HOST_COMPILER STREQUAL CMAKE_C_COMPILER AND CMAKE_C_COMPILER_ID STREQUAL "Clang")
    message(WARNING "CUDA_HOST_COMPILER is set to an unsupported compiler: ${CMAKE_C_COMPILER}.  See http://dev.pointclouds.org/issues/979")
  endif()
endif()

if (UNIX OR APPLE)
  set (CUDA_NVCC_FLAGS ${CUDA_NVCC_FLAGS}  "-Xcompiler;-fPIC;")     
endif()
set(CUDA_NVCC_FLAGS ${CUDA_NVCC_FLAGS}  "--ftz=true;--prec-div=false;--prec-sqrt=false -arch sm_20") 

## Declare a cpp library
file(GLOB srcs src/*.cpp)
file(GLOB cuda src/cuda/*.cu)

CUDA_COMPILE(cuda_objs ${cuda})

add_library(scanner
	${srcs}
	${cuda}
	${cuda_objs}
)
target_link_libraries(scanner 	
	${CUDA_LIBRARIES}
	${OpenCV_LIBS}
	${OPENNI_LIBRARIES}
)

add_executable(vm_scanner tools/vm_scanner.cpp)
target_link_libraries(vm_scanner
	scanner
	${OpenCV_LIBS}
)

#############
## Install ##
#############

# Mark executables and/or libraries for installation
install(TARGETS scanner vm_scanner
  ARCHIVE DESTINATION ${ALPINE_PROJECT_LIB_DESTINATION}
  LIBRARY DESTINATION ${ALPINE_PROJECT_LIB_DESTINATION}
  RUNTIME DESTINATION ${ALPINE_GLOBAL_BIN_DESTINATION}
)

# Mark cpp header files for installation
install(DIRECTORY include/${PROJECT_NAME}/
  DESTINATION ${ALPINE_PROJECT_INCLUDE_DESTINATION}
)