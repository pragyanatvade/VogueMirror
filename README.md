# VogueMirror
Project creates 3D model of human being while he is scanned with the help of kinect sensor.
Demo of the project is shown at https://www.youtube.com/watch?v=w4Rc0apddmo.

# Under The Hood
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
