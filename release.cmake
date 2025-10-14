# Copyright (C) 2008-2014,2018 LAAS-CNRS, JRL AIST-CNRS.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

# .rst: .. command:: RELEASE_SETUP
#
# .. _target-release:
#
# This adds a *release* target which release a stable version of the current
# package.
#
# To release a package, please run:
#
# .. code-block:: bash
#
# make release VERSION=X.Y.Z
#
# where ``X.Y.Z`` is the version number of your new package.
#
# A release consists in:
#
# * adding a signed tag following the ``vVERSION`` pattern.
# * running ``make distcheck`` (:ref:`distcheck <target-distcheck>`) to make
#   sure everything is ok.
# * running ``make dist`` to generate a tarball
# * running ``make distclean`` to remove the current dist directory
# * reminds that you should push the tag and tarball on the GitHub repository
#   (to be done manually as it is simple but cannot be reverted).
#
# .. todo::
#
# The following steps are missing to the current release procedure:
#
# * uploading the stable documentation.
# * uploading the resulting tarball to GitHub.
# * announce the release by e-mail.
#
macro(RELEASE_SETUP)
  if(UNIX)
    if(NOT TARGET release)
      add_custom_target(release COMMENT "Create a new release")
    endif()
    
    add_custom_target(
      ${PROJECT_NAME}-release
      WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
      COMMENT "Create a new release for ${PROJECT_NAME}"
      COMMAND
        export LD_LIBRARY_PATH=$ENV{LD_LIBRARY_PATH} &&
        export DYLD_LIBRARY_PATH=$ENV{DYLD_LIBRARY_PATH} &&
        export PYTHONPATH=$ENV{PYTHONPATH} &&
        ${PYTHON_EXECUTABLE} ${PROJECT_JRL_CMAKE_MODULE_DIR}/release.py
        $$VERSION
        --source-dir ${PROJECT_SOURCE_DIR}
        --binary-dir ${PROJECT_BINARY_DIR}
        --project-name ${PROJECT_NAME}
        --python-executable ${PYTHON_EXECUTABLE}
        --cmake-module-dir ${PROJECT_JRL_CMAKE_MODULE_DIR}
    )
    
    add_dependencies(release ${PROJECT_NAME}-release)
  endif()
endmacro()
