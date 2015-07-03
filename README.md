# VogueMirror
Project creates 3D model of human being while he is scanned with the help of kinect sensor.
Demo of the project is shown at https://www.youtube.com/watch?v=w4Rc0apddmo.

# Directory Structure
As per the directory structure:

```
/VogueMirror
--- /vm_deps: List of open source dependencies.
------ /OpenNI: OpenNI driver to run kinect sensor on ubuntu. Modified to run on Ubuntu 14.04
------ /SensorKinect: Package used by OpenNI so that kinect could function properly.
------ /alpine_pkg: Python library to retrieve information about alpine projects.
--- /voguemirror: List of main modules written called as alpine modules.
------ /alpine: A build system to compile multiple projects with single invocation and resolving inter module dependencies
------ /cmake_modules: Collection of CMake modules which are commonly used in alpine modules.
------ /scanner: Alpine module provides classes and tools for 3D scanning.
--- /others: OpenCV 3.0.0 is another opensource library on which this project is dependent.
```

# Modules written by me
alpine_pkg: A dependency for alpine build system to parse XML manifest file and create topological order of different projects to build them properly.

alpine: Alpine build system is a project targetted at creating a build system which could build multiple python and CPP projects with single invocation and create executables and libraries available to the host system immediately. It turns out to be just a collection of CMake macros and associated python code used for building

cmake_modules: An alpine module which provides various CMake modules to alpine workspace which in turn can directly be used in other alpine projects. Provided CMake modules are:

```
FindEigen.cmake, FindFLANN.cmake, FindMPI.cmake, FindOpenNI.cmake, Findlibusb-1.0.cmake
```

scanner: Main module which is responsible for creating 3D human model. It uses [Kintinuous](http://www.cs.nuim.ie/research/vision/data/rgbd2012/) algorithm implemented on GPU with CUDA.
