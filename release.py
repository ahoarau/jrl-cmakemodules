#!/usr/bin/env python3
"""
Release script for jrl-cmakemodules projects.

This script automates the release process including:
- Updating version in package.xml
- Updating version in pyproject.toml
- Updating CHANGELOG.md
- Updating version in pixi.toml
- Updating version and date in CITATION.cff
- Creating a signed git tag
- Running distcheck, dist, and distclean targets
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def run_command(cmd, cwd=None, check=True, capture_output=False):
    """Run a shell command."""
    print(f"Running: {cmd}")
    if isinstance(cmd, str):
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=check,
            capture_output=capture_output, text=True
        )
    else:
        result = subprocess.run(
            cmd, cwd=cwd, check=check,
            capture_output=capture_output, text=True
        )
    return result


def git_add_and_commit(file_path, version, message_suffix):
    """Add a file to git and commit it."""
    run_command(["git", "add", file_path])
    commit_msg = f"release: {message_suffix} to {version}"
    run_command(["git", "commit", "-m", commit_msg])
    print(f"Updated {file_path} and committed")


def update_package_xml(version, source_dir):
    """Update version in package.xml."""
    package_xml = Path(source_dir) / "package.xml"
    if not package_xml.exists():
        return False
    
    print(f"Updating {package_xml}...")
    content = package_xml.read_text()
    new_content = re.sub(
        r'<version>.*?</version>',
        f'<version>{version}</version>',
        content
    )
    package_xml.write_text(new_content)
    
    # Check if there were changes
    result = run_command(
        ["git", "diff", "--quiet", "package.xml"],
        cwd=source_dir, check=False
    )
    if result.returncode != 0:
        git_add_and_commit("package.xml", version, "Update package.xml version")
        return True
    return False


def update_pyproject_toml(version, source_dir, python_executable, cmake_module_dir):
    """Update version in pyproject.toml."""
    pyproject_toml = Path(source_dir) / "pyproject.toml"
    if not pyproject_toml.exists():
        return False
    
    print(f"Updating {pyproject_toml}...")
    pyproject_script = Path(cmake_module_dir) / "pyproject.py"
    run_command([python_executable, str(pyproject_script), version], cwd=source_dir)
    
    # Check if there were changes
    result = run_command(
        ["git", "diff", "--quiet", "pyproject.toml"],
        cwd=source_dir, check=False
    )
    if result.returncode != 0:
        git_add_and_commit("pyproject.toml", version, "Update pyproject.toml version")
        return True
    return False


def update_changelog(version, source_dir):
    """Update CHANGELOG.md."""
    changelog = Path(source_dir) / "CHANGELOG.md"
    if not changelog.exists():
        return False
    
    print(f"Updating {changelog}...")
    today = date.today().strftime("%Y-%m-%d")
    content = changelog.read_text()
    
    # Add new version section after [Unreleased]
    new_content = re.sub(
        r'## \[Unreleased\]',
        f'## [Unreleased]\n\n## [{version}] - {today}',
        content,
        count=1
    )
    
    # Update the comparison links at the bottom
    new_content = re.sub(
        r'\[Unreleased\]: (https://.*compare/)(v.*?)\.\.\.HEAD',
        f'[Unreleased]: \\1v{version}...HEAD\n[{version}]: \\1\\2...v{version}',
        new_content,
        count=1
    )
    
    changelog.write_text(new_content)
    
    # Check if there were changes
    result = run_command(
        ["git", "diff", "--quiet", "CHANGELOG.md"],
        cwd=source_dir, check=False
    )
    if result.returncode != 0:
        git_add_and_commit("CHANGELOG.md", version, "Update CHANGELOG.md for")
        return True
    return False


def update_pixi_toml(version, source_dir, python_executable, cmake_module_dir):
    """Update version in pixi.toml."""
    pixi_toml = Path(source_dir) / "pixi.toml"
    if not pixi_toml.exists():
        return False
    
    print(f"Updating {pixi_toml}...")
    pixi_script = Path(cmake_module_dir) / "pixi.py"
    run_command([python_executable, str(pixi_script), version], cwd=source_dir)
    
    # Check if there were changes
    result = run_command(
        ["git", "diff", "--quiet", "pixi.toml"],
        cwd=source_dir, check=False
    )
    if result.returncode != 0:
        git_add_and_commit("pixi.toml", version, "Update pixi.toml version")
        return True
    return False


def update_citation_cff(version, source_dir):
    """Update version and date in CITATION.cff."""
    citation_cff = Path(source_dir) / "CITATION.cff"
    if not citation_cff.exists():
        return False
    
    print(f"Updating {citation_cff}...")
    today = date.today().strftime("%Y-%m-%d")
    content = citation_cff.read_text()
    
    # Update version
    new_content = re.sub(r'^version:.*', f'version: {version}', content, flags=re.MULTILINE)
    # Update date-released
    new_content = re.sub(
        r'^date-released:.*',
        f'date-released: "{today}"',
        new_content,
        flags=re.MULTILINE
    )
    
    citation_cff.write_text(new_content)
    git_add_and_commit("CITATION.cff", version, "Update CITATION.cff version")
    return True


def create_git_tag(version, source_dir):
    """Create a signed git tag."""
    tag_name = f"v{version}"
    print(f"Creating signed tag {tag_name}...")
    run_command(["git", "tag", "-s", tag_name, "-m", f"Release of version {version}."], cwd=source_dir)


def run_distcheck(project_name, binary_dir, source_dir):
    """Run distcheck target."""
    print("Running distcheck...")
    build_cmd = ["cmake", "--build", binary_dir, "--target", f"{project_name}-distcheck"]
    try:
        run_command(build_cmd)
    except subprocess.CalledProcessError:
        print("ERROR: distcheck failed. Removing tag...")
        version = None
        # Try to get the version from the tag we just created
        result = run_command(
            ["git", "tag", "--list", "v*", "--sort=-version:refname"],
            cwd=source_dir, capture_output=True
        )
        if result.stdout:
            latest_tag = result.stdout.strip().split('\n')[0]
            if latest_tag.startswith('v'):
                version = latest_tag[1:]
                run_command(["git", "tag", "-d", f"v{version}"], cwd=source_dir)
        raise


def run_dist_and_distclean(project_name, binary_dir):
    """Run dist and distclean targets."""
    print("Running dist...")
    run_command(["cmake", "--build", binary_dir, "--target", f"{project_name}-dist"])
    
    print("Running distclean...")
    run_command(["cmake", "--build", binary_dir, "--target", f"{project_name}-distclean"])


def main():
    parser = argparse.ArgumentParser(
        description="Release script for jrl-cmakemodules projects"
    )
    parser.add_argument("version", help="Version number for the release (e.g., 1.2.3)")
    parser.add_argument("--source-dir", required=True, help="Source directory path")
    parser.add_argument("--binary-dir", required=True, help="Binary directory path")
    parser.add_argument("--project-name", required=True, help="Project name")
    parser.add_argument("--python-executable", required=True, help="Python executable path")
    parser.add_argument("--cmake-module-dir", required=True, help="CMake module directory path")
    
    args = parser.parse_args()
    
    # Validate version is provided
    if not args.version:
        print("ERROR: Please set a version for this release", file=sys.stderr)
        return 1
    
    version = args.version
    source_dir = args.source_dir
    binary_dir = args.binary_dir
    project_name = args.project_name
    python_executable = args.python_executable
    cmake_module_dir = args.cmake_module_dir
    
    print(f"Creating release {version} for {project_name}")
    print(f"Source directory: {source_dir}")
    print(f"Binary directory: {binary_dir}")
    
    try:
        # Update all version files
        update_package_xml(version, source_dir)
        update_pyproject_toml(version, source_dir, python_executable, cmake_module_dir)
        update_changelog(version, source_dir)
        update_pixi_toml(version, source_dir, python_executable, cmake_module_dir)
        update_citation_cff(version, source_dir)
        
        # Create git tag
        create_git_tag(version, source_dir)
        
        # Reconfigure cmake to pick up new version
        print("Reconfiguring CMake...")
        run_command(["cmake", source_dir], cwd=binary_dir)
        
        # Run distcheck
        run_distcheck(project_name, binary_dir, source_dir)
        
        # Run dist and distclean
        run_dist_and_distclean(project_name, binary_dir)
        
        print("\n" + "=" * 70)
        print("SUCCESS! Release created.")
        print("=" * 70)
        print("Please, run 'git push --tags' and upload the tarball to github")
        print("to finalize this release.")
        print("=" * 70)
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Command failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
