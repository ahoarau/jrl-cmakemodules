# Install script for directory: /home/runner/work/jrl-cmakemodules/jrl-cmakemodules

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/jrl/cmakemodules" TYPE FILE PERMISSIONS OWNER_READ GROUP_READ WORLD_READ OWNER_WRITE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/include/jrl/cmakemodules/config.hh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/jrl/cmakemodules" TYPE FILE PERMISSIONS OWNER_READ GROUP_READ WORLD_READ OWNER_WRITE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/include/jrl/cmakemodules/deprecated.hh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/jrl/cmakemodules" TYPE FILE PERMISSIONS OWNER_READ GROUP_READ WORLD_READ OWNER_WRITE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/include/jrl/cmakemodules/warning.hh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/jrl-cmakemodules" TYPE DIRECTORY FILES
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./boost"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./cython"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./doxygen"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./dynamic_graph"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./find-external"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./github"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./gtest"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./hpp"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./image"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./sphinx"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./stubgen"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./_unittests"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/jrl-cmakemodules" TYPE PROGRAM FILES
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./announce-gen"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./fix-license.sh"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./git-archive-all.py"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./git-archive-all.sh"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./gitlog-to-changelog"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./pixi.py"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./pyproject.py"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./release.py"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/jrl-cmakemodules" TYPE FILE FILES
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./apple.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./base.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./boost.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./catkin.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./CMakeLists.txt"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./cmake_reinstall.cmake.in"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./cmake_uninstall.cmake.in"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./compiler.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./componentConfig.cmake.in"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./Config.cmake.in"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./config.h.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./config.hh.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./coverage.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./cpack.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./createshexe.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./cxx11.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./cxx-standard.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./debian.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./deprecated.hh.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./distcheck.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./dist.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./doxygen.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./eigen.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./filefilter.txt"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./flake.lock"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./flake.nix"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./geometric-tools.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./GNUInstallDirs.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./gtest.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./header.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./hpp.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./ide.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./idl.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./idlrtc.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./install-data.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./install-helpers.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./julia.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./kineo.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./lapack.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./LICENSE"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./logging.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./man.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./memorycheck_unit_test.cmake.in"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./metapodfromurdf.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./modernize-links.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./msvc-specific.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./msvc.vcxproj.user.in"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./openhrp.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./openhrpcontroller.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./openrtm.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./oscheck.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./package-config.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./package.xml"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./pkg-config.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./pkg-config.pc.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./portability.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./post-project.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./pthread.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./python.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./python-helpers.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./qhull.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./README.md"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./release.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./relpath.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./ros2.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./ros.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./sdformat.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./setup.cfg"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./shared-library.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./sphinx.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./stubs.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./swig.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./test.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./tracy.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./tracy.hh.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./uninstall.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./version.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./version-script.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./version-script-test.lds"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./warning.hh.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/./xacro.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/jrl-cmakemodules" TYPE FILE FILES
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/generated/jrl-cmakemodulesConfig.cmake"
    "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/generated/jrl-cmakemodulesConfigVersion.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/jrl-cmakemodules/jrl-cmakemodulesTargets.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/jrl-cmakemodules/jrl-cmakemodulesTargets.cmake"
         "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/CMakeFiles/Export/e7cd96a2922871471f510b601bd9d589/jrl-cmakemodulesTargets.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/jrl-cmakemodules/jrl-cmakemodulesTargets-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/jrl-cmakemodules/jrl-cmakemodulesTargets.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/jrl-cmakemodules" TYPE FILE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/CMakeFiles/Export/e7cd96a2922871471f510b601bd9d589/jrl-cmakemodulesTargets.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE PERMISSIONS OWNER_READ GROUP_READ WORLD_READ OWNER_WRITE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/jrl-cmakemodules.pc")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/packages" TYPE FILE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/share/ament_index/resource_index/packages/jrl-cmakemodules")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/jrl-cmakemodules/hook" TYPE FILE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/share/jrl-cmakemodules/hook/ament_prefix_path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/jrl-cmakemodules/hook" TYPE FILE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/share/jrl-cmakemodules/hook/python_path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/jrl-cmakemodules" TYPE FILE FILES "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/package.xml")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
if(CMAKE_INSTALL_COMPONENT)
  if(CMAKE_INSTALL_COMPONENT MATCHES "^[a-zA-Z0-9_.+-]+$")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
  else()
    string(MD5 CMAKE_INST_COMP_HASH "${CMAKE_INSTALL_COMPONENT}")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INST_COMP_HASH}.txt")
    unset(CMAKE_INST_COMP_HASH)
  endif()
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/home/runner/work/jrl-cmakemodules/jrl-cmakemodules/build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
