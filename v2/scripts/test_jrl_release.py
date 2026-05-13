#!/usr/bin/env uv run --no-project
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pytest>=8.4.2",
#     "pytest-cov>=5.0.0",
#     "pytest-mock>=3.12.0",
#     # The following dependencies must be kept in sync with jrl_release.py
#     "tomlkit",
#     "ruamel.yaml",
#     "rich",
#     "GitPython",
#     "cmake-parser",
# ]
# ///

"""
Comprehensive unit tests for jrl_release.py.

Run with:
    uv run test_jrl_release.py               # Run all tests
    uv run test_jrl_release.py -v            # Verbose output
    uv run test_jrl_release.py -k test_xml   # Run specific tests
"""

import sys
import re
import json
import subprocess
import argparse
from pathlib import Path
from io import BytesIO, StringIO
from datetime import date
from unittest.mock import Mock

import pytest
from rich.console import Console

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent))
import jrl_release as release


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def reset_release_console():
    """Use a fresh console for each test.

    Some CLI paths rebind the module-level console to stderr/stdout-aware streams.
    Resetting it between tests keeps direct function tests deterministic.
    """
    original_console = release.console
    release.console = Console()
    yield
    release.console = original_console


@pytest.fixture
def sample_package_xml(tmp_path):
    """Create a sample package.xml file."""
    content = """<?xml version="1.0"?>
<package format="2">
  <name>test_package</name>
  <version>1.0.0</version>
  <description>Test package</description>
</package>"""
    file_path = tmp_path / "package.xml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_pyproject_toml(tmp_path):
    """Create a sample pyproject.toml file."""
    content = """[project]
name = "test-project"
version = "1.0.0"
description = "Test project"
"""
    file_path = tmp_path / "pyproject.toml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_poetry_pyproject_toml(tmp_path):
    """Create a sample pyproject.toml file with Poetry format."""
    content = """[tool.poetry]
name = "test-project"
version = "2.5.10"
description = "Test project with Poetry"
"""
    file_path = tmp_path / "pyproject.toml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_pixi_toml(tmp_path):
    """Create a sample pixi.toml file."""
    content = """[workspace]
version = "1.0.0"
name = "test-workspace"
"""
    file_path = tmp_path / "pixi.toml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_citation_cff(tmp_path):
    """Create a sample CITATION.cff file."""
    content = """cff-version: 1.2.0
title: "Test Project"
version: 1.0.0
date-released: "2024-01-01"
"""
    file_path = tmp_path / "CITATION.cff"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_cmake_lists(tmp_path):
    """Create a sample CMakeLists.txt file."""
    content = """cmake_minimum_required(VERSION 3.10)
project(TestProject VERSION 1.0.0 DESCRIPTION "A test project")

add_library(testlib src/test.cpp)
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_changelog(tmp_path):
    """Create a sample CHANGELOG.md file."""
    content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature coming soon

## [1.0.0] - 2024-01-15

### Added
- Initial release
"""
    file_path = tmp_path / "CHANGELOG.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def malformed_xml(tmp_path):
    """Create a malformed XML file."""
    content = """<?xml version="1.0"?>
<package>
  <name>broken</name>
  <!-- Missing version tag -->
</package>"""
    file_path = tmp_path / "broken.xml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def malformed_toml(tmp_path):
    """Create a malformed TOML file."""
    content = """[project
name = "broken"
# Missing closing bracket
"""
    file_path = tmp_path / "broken.toml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def project_dir(
    tmp_path,
    sample_package_xml,
    sample_pyproject_toml,
    sample_pixi_toml,
    sample_citation_cff,
    sample_cmake_lists,
    sample_changelog,
):
    """Create a complete project directory with all version files."""
    # Files are already created in tmp_path by the fixtures
    return tmp_path


# ============================================================================
# TEST VersionExtractor Base Class
# ============================================================================


def test_version_extractor_properties(sample_package_xml):
    """Test VersionExtractor base properties."""
    extractor = release.XmlVersionExtractor(sample_package_xml)
    assert extractor.file_path == sample_package_xml
    assert extractor.name == "package.xml"
    assert extractor.path == str(sample_package_xml)


def test_version_extractor_file_exists(tmp_path):
    """Test check_file_exists method."""
    extractor = release.XmlVersionExtractor(tmp_path / "package.xml")
    assert not extractor.check_file_exists()

    # Create the file
    (tmp_path / "package.xml").write_text("<version>1.0.0</version>")
    assert extractor.check_file_exists()


# ============================================================================
# TEST XmlVersionExtractor
# ============================================================================


def test_xml_extractor_get_version(sample_package_xml):
    """Test XmlVersionExtractor can read version."""
    extractor = release.XmlVersionExtractor(sample_package_xml)
    assert extractor.get_version() == "1.0.0"


def test_xml_extractor_update_version(sample_package_xml):
    """Test XmlVersionExtractor can update version."""
    extractor = release.XmlVersionExtractor(sample_package_xml)
    extractor.update_version("2.3.4")

    # Verify the update
    assert extractor.get_version() == "2.3.4"

    # Verify structure is preserved
    content = sample_package_xml.read_text(encoding="utf-8")
    assert "<name>test_package</name>" in content
    assert "<version>2.3.4</version>" in content


def test_xml_extractor_missing_version_tag(malformed_xml):
    """Test XmlVersionExtractor raises VersionNotPresent for missing version tag."""
    extractor = release.XmlVersionExtractor(malformed_xml)
    with pytest.raises(release.VersionNotPresent, match="No <version> tag found"):
        extractor.get_version()


def test_xml_extractor_multiple_version_tags(tmp_path):
    """Test XmlVersionExtractor only updates first version tag."""
    content = """<?xml version="1.0"?>
<package>
  <version>1.0.0</version>
  <depends>
    <package version="0.5.0"/>
  </depends>
</package>"""
    file_path = tmp_path / "multi_version.xml"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.XmlVersionExtractor(file_path)
    extractor.update_version("2.0.0")

    updated_content = file_path.read_text(encoding="utf-8")
    assert "<version>2.0.0</version>" in updated_content
    assert '<package version="0.5.0"/>' in updated_content  # Should remain unchanged


# ============================================================================
# TEST TomlVersionExtractor
# ============================================================================


def test_toml_extractor_get_version(sample_pyproject_toml):
    """Test TomlVersionExtractor can read version from pyproject.toml."""
    extractor = release.TomlVersionExtractor(
        sample_pyproject_toml, ["project", "version"]
    )
    assert extractor.get_version() == "1.0.0"


def test_toml_extractor_poetry_format(sample_poetry_pyproject_toml):
    """Test TomlVersionExtractor with Poetry format."""
    extractor = release.TomlVersionExtractor(
        sample_poetry_pyproject_toml, ["tool", "poetry", "version"]
    )
    assert extractor.get_version() == "2.5.10"


def test_toml_extractor_update_version(sample_pyproject_toml):
    """Test TomlVersionExtractor can update version."""
    extractor = release.TomlVersionExtractor(
        sample_pyproject_toml, ["project", "version"]
    )
    extractor.update_version("3.1.4")

    assert extractor.get_version() == "3.1.4"

    # Verify structure is preserved
    content = sample_pyproject_toml.read_text(encoding="utf-8")
    assert 'name = "test-project"' in content


def test_toml_extractor_pixi_format(sample_pixi_toml):
    """Test TomlVersionExtractor with pixi.toml format."""
    extractor = release.TomlVersionExtractor(sample_pixi_toml, ["workspace", "version"])
    assert extractor.get_version() == "1.0.0"

    extractor.update_version("1.2.3")
    assert extractor.get_version() == "1.2.3"


def test_toml_extractor_missing_key(sample_pyproject_toml):
    """Test TomlVersionExtractor raises VersionNotPresent for missing key."""
    extractor = release.TomlVersionExtractor(
        sample_pyproject_toml, ["nonexistent", "key"]
    )
    with pytest.raises(
        release.VersionNotPresent, match="Key 'nonexistent.key' not found"
    ):
        extractor.get_version()


def test_toml_extractor_preserves_formatting(tmp_path):
    """Test TomlVersionExtractor preserves TOML formatting."""
    content = """# Comment preserved
[project]
name = "test"  # inline comment
version = "1.0.0"

[tool.other]
key = "value"
"""
    file_path = tmp_path / "formatted.toml"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.TomlVersionExtractor(file_path, ["project", "version"])
    extractor.update_version("2.0.0")

    updated = file_path.read_text(encoding="utf-8")
    assert "# Comment preserved" in updated
    assert "# inline comment" in updated
    assert 'version = "2.0.0"' in updated


# ============================================================================
# TEST YamlVersionExtractor
# ============================================================================


def test_yaml_extractor_get_version(sample_citation_cff):
    """Test YamlVersionExtractor can read version."""
    extractor = release.YamlVersionExtractor(sample_citation_cff, ["version"])
    assert extractor.get_version() == "1.0.0"


def test_yaml_extractor_update_version(sample_citation_cff):
    """Test YamlVersionExtractor can update version."""
    extractor = release.YamlVersionExtractor(sample_citation_cff, ["version"])
    extractor.update_version("2.1.0")

    assert extractor.get_version() == "2.1.0"

    # Verify other fields are preserved
    content = sample_citation_cff.read_text(encoding="utf-8")
    assert "cff-version: 1.2.0" in content
    assert 'title: "Test Project"' in content or "title: 'Test Project'" in content


def test_yaml_extractor_missing_key(sample_citation_cff):
    """Test YamlVersionExtractor raises VersionNotPresent for missing key."""
    extractor = release.YamlVersionExtractor(sample_citation_cff, ["nonexistent"])
    with pytest.raises(release.VersionNotPresent, match="Key 'nonexistent' not found"):
        extractor.get_version()


def test_yaml_extractor_nested_key(tmp_path):
    """Test YamlVersionExtractor with nested keys."""
    content = """metadata:
  release:
    version: 3.2.1
"""
    file_path = tmp_path / "nested.yaml"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.YamlVersionExtractor(
        file_path, ["metadata", "release", "version"]
    )
    assert extractor.get_version() == "3.2.1"

    extractor.update_version("4.0.0")
    assert extractor.get_version() == "4.0.0"


# ============================================================================
# TEST CMakeListsVersionExtractor
# ============================================================================


def test_cmake_extractor_get_version_simple(sample_cmake_lists):
    """Test CMakeListsVersionExtractor can extract version from simple CMakeLists.txt."""
    extractor = release.CMakeListsVersionExtractor(sample_cmake_lists)
    assert extractor.get_version() == "1.0.0"


def test_cmake_extractor_get_version_multiline(tmp_path):
    """Test CMakeListsVersionExtractor with multiline project()."""
    content = """cmake_minimum_required(VERSION 3.22)

project(
  TestProject
  DESCRIPTION "JRL CMake utility toolbox"
  HOMEPAGE_URL "http://github.com/example/project"
  VERSION 2.5.10
  LANGUAGES CXX
)

add_library(testlib src/test.cpp)
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.CMakeListsVersionExtractor(file_path)
    assert extractor.get_version() == "2.5.10"


def test_cmake_extractor_with_fallback_version(tmp_path):
    """Test CMakeListsVersionExtractor with PROJECT_VERSION variable and fallback."""
    content = """cmake_minimum_required(VERSION 3.22)

# Read version from package.xml if available
set(PROJECT_VERSION "3.1.4") # Default fallback version
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/package.xml")
  file(READ "${CMAKE_CURRENT_SOURCE_DIR}/package.xml" PACKAGE_XML_CONTENT)
  string(REGEX MATCH "<version>([0-9]+\\.[0-9]+\\.[0-9]+)</version>" _ "${PACKAGE_XML_CONTENT}")
  if(CMAKE_MATCH_1)
    set(PROJECT_VERSION "${CMAKE_MATCH_1}")
  endif()
endif()

project(
  TestProject
  DESCRIPTION "Test project"
  VERSION ${PROJECT_VERSION}
  LANGUAGES NONE
)
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.CMakeListsVersionExtractor(file_path)
    # Should extract from the fallback set(PROJECT_VERSION "3.1.4")
    assert extractor.get_version() == "3.1.4"


def test_cmake_extractor_update_version_simple(sample_cmake_lists):
    """Test CMakeListsVersionExtractor can update version in simple CMakeLists.txt."""
    extractor = release.CMakeListsVersionExtractor(sample_cmake_lists)
    extractor.update_version("2.0.0")

    # Verify the update
    assert extractor.get_version() == "2.0.0"

    # Verify structure is preserved
    content = sample_cmake_lists.read_text(encoding="utf-8")
    assert "cmake_minimum_required" in content
    assert "add_library" in content
    assert 'DESCRIPTION "A test project"' in content


def test_cmake_extractor_update_version_multiline(tmp_path):
    """Test CMakeListsVersionExtractor can update version in multiline project()."""
    content = """cmake_minimum_required(VERSION 3.22)

project(
  TestProject
  DESCRIPTION "Test project"
  VERSION 1.0.0
  LANGUAGES CXX
)
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.CMakeListsVersionExtractor(file_path)
    extractor.update_version("1.2.3")

    assert extractor.get_version() == "1.2.3"
    content = file_path.read_text(encoding="utf-8")
    assert "VERSION 1.2.3" in content


def test_cmake_extractor_update_fallback_version(tmp_path):
    """Test CMakeListsVersionExtractor updates both fallback and project version."""
    content = """cmake_minimum_required(VERSION 3.22)

set(PROJECT_VERSION "1.0.0")

project(
  TestProject
  VERSION ${PROJECT_VERSION}
  LANGUAGES NONE
)
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.CMakeListsVersionExtractor(file_path)
    extractor.update_version("2.5.0")

    # Check that fallback was updated
    content = file_path.read_text(encoding="utf-8")
    assert 'set(PROJECT_VERSION "2.5.0")' in content


def test_cmake_extractor_no_version_found(tmp_path):
    """Test CMakeListsVersionExtractor raises error when no version found."""
    content = """cmake_minimum_required(VERSION 3.10)
project(TestProject DESCRIPTION "No version here")
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.CMakeListsVersionExtractor(file_path)
    with pytest.raises(release.VersionNotPresent, match="No version found"):
        extractor.get_version()


def test_cmake_extractor_preserves_structure(tmp_path):
    """Test CMakeListsVersionExtractor preserves file structure and formatting."""
    content = """# This is a comment
cmake_minimum_required(VERSION 3.22)

# Another comment
project(
  TestProject
  VERSION 1.5.2
  DESCRIPTION "Test"
  LANGUAGES CXX
)

# Build configuration
set(CMAKE_CXX_STANDARD 17)
add_library(mylib src/lib.cpp)
"""
    file_path = tmp_path / "CMakeLists.txt"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.CMakeListsVersionExtractor(file_path)
    extractor.update_version("1.5.3")

    content = file_path.read_text(encoding="utf-8")
    # Check comments are preserved
    assert "# This is a comment" in content
    assert "# Another comment" in content
    assert "# Build configuration" in content
    # Check other settings preserved
    assert "CMAKE_CXX_STANDARD" in content
    assert "add_library" in content
    # Check version updated
    assert "VERSION 1.5.3" in content


# ============================================================================
# TEST ChangelogVersionExtractor
# ============================================================================


def test_changelog_extractor_get_version(sample_changelog):
    """Test ChangelogVersionExtractor can read version."""
    extractor = release.ChangelogVersionExtractor(sample_changelog, "")
    assert extractor.get_version() == "1.0.0"


def test_changelog_extractor_update_version(sample_changelog, capsys):
    """Test ChangelogVersionExtractor can update version."""
    extractor = release.ChangelogVersionExtractor(sample_changelog, "")
    extractor.update_version("1.1.0")

    content = sample_changelog.read_text(encoding="utf-8")
    today = date.today().isoformat()

    # Should have both Unreleased and new version
    assert "## [Unreleased]" in content
    assert f"## [1.1.0] - {today}" in content
    assert "## [1.0.0] - 2024-01-15" in content

    # New version should be after Unreleased
    unreleased_idx = content.index("## [Unreleased]")
    new_version_idx = content.index(f"## [1.1.0] - {today}")
    assert unreleased_idx < new_version_idx


def test_changelog_extractor_no_unreleased(tmp_path, capsys):
    """Test ChangelogVersionExtractor with no Unreleased section."""
    content = """# Changelog

## [1.0.0] - 2024-01-01

Initial release
"""
    file_path = tmp_path / "CHANGELOG.md"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.ChangelogVersionExtractor(file_path, "")
    extractor.update_version("1.1.0")

    # Content should be unchanged
    assert file_path.read_text() == content


def test_changelog_extractor_no_released_version(tmp_path):
    """Test ChangelogVersionExtractor with only Unreleased."""
    content = """# Changelog

## [Unreleased]

- Some changes
"""
    file_path = tmp_path / "CHANGELOG.md"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.ChangelogVersionExtractor(file_path, "")
    with pytest.raises(release.VersionNotPresent, match="No released version found"):
        extractor.get_version()


def test_changelog_extractor_multiple_versions(tmp_path):
    """Test ChangelogVersionExtractor returns first non-Unreleased version."""
    content = """# Changelog

## [Unreleased]

## [2.0.0] - 2024-02-01

## [1.5.0] - 2024-01-15

## [1.0.0] - 2024-01-01
"""
    file_path = tmp_path / "CHANGELOG.md"
    file_path.write_text(content, encoding="utf-8")

    extractor = release.ChangelogVersionExtractor(file_path, "")
    # Should get the first non-Unreleased version
    assert extractor.get_version() == "2.0.0"


# ============================================================================
# TEST Validation Functions
# ============================================================================


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1.0.0", (1, 0, 0)),
        ("2.5.10", (2, 5, 10)),
        ("0.0.1", (0, 0, 1)),
        ("999.888.777", (999, 888, 777)),
    ],
)
def test_parse_semver_valid(version, expected):
    """Test parsing valid semver strings."""
    assert release.parse_semver(version) == expected


@pytest.mark.parametrize(
    "invalid_version",
    [
        "1.2",
        "1.2.3.4",
        "v1.2.3",
        "1.2.a",
        "abc",
        "1.2.3-alpha",
        "1.2.3+build",
    ],
)
def test_parse_semver_invalid(invalid_version):
    """Test parsing invalid semver strings."""
    with pytest.raises(ValueError, match="Invalid semver format"):
        release.parse_semver(invalid_version)


@pytest.mark.parametrize(
    "version,bump_type,expected",
    [
        ("1.0.0", "major", "2.0.0"),
        ("1.0.0", "minor", "1.1.0"),
        ("1.0.0", "patch", "1.0.1"),
        ("2.5.10", "major", "3.0.0"),
        ("2.5.10", "minor", "2.6.0"),
        ("2.5.10", "patch", "2.5.11"),
        ("0.0.1", "patch", "0.0.2"),
    ],
)
def test_bump_version_valid(version, bump_type, expected):
    """Test version bumping."""
    assert release.bump_version(version, bump_type) == expected


def test_bump_version_invalid_type():
    """Test bump_version with invalid bump type."""
    with pytest.raises(ValueError, match="Invalid bump type"):
        release.bump_version("1.0.0", "invalid")


def test_validate_semver_valid():
    """Test validate_semver accepts valid versions."""
    assert release.validate_semver("1.2.3") == "1.2.3"


def test_validate_semver_invalid():
    """Test validate_semver rejects invalid versions."""
    with pytest.raises(argparse.ArgumentTypeError):
        release.validate_semver("invalid")


# ============================================================================
# TEST Version Checking Functions
# ============================================================================


def test_get_current_version_all_match(project_dir):
    """Test get_current_version when all files have same version."""
    checks = [
        release.XmlVersionExtractor(project_dir / "package.xml"),
        release.TomlVersionExtractor(
            project_dir / "pyproject.toml", ["project", "version"]
        ),
    ]

    version = release.get_current_version(checks)
    assert version == "1.0.0"


def test_get_current_version_mismatch(tmp_path, capsys):
    """Test get_current_version with version mismatch."""
    (tmp_path / "package.xml").write_text("<version>1.0.0</version>")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "2.0.0"\n')

    checks = [
        release.XmlVersionExtractor(tmp_path / "package.xml"),
        release.TomlVersionExtractor(
            tmp_path / "pyproject.toml", ["project", "version"]
        ),
    ]

    version = release.get_current_version(checks)
    assert version is None


def test_get_current_version_no_files(tmp_path, capsys):
    """Test get_current_version when no files exist."""
    checks = [
        release.XmlVersionExtractor(tmp_path / "package.xml"),
        release.TomlVersionExtractor(
            tmp_path / "pyproject.toml", ["project", "version"]
        ),
    ]

    version = release.get_current_version(checks)
    assert version is None


def test_get_current_version_some_missing(tmp_path):
    """Test get_current_version when some files are missing."""
    (tmp_path / "package.xml").write_text("<version>3.2.1</version>")
    # pyproject.toml doesn't exist

    checks = [
        release.XmlVersionExtractor(tmp_path / "package.xml"),
        release.TomlVersionExtractor(
            tmp_path / "pyproject.toml", ["project", "version"]
        ),
    ]

    version = release.get_current_version(checks)
    assert version == "3.2.1"


def test_show_version_diff_capture_output():
    """Test show_version_diff produces output."""
    string_io = StringIO()
    test_console = Console(file=string_io)

    # Temporarily replace global console
    old_console = release.console
    release.console = test_console

    try:
        release.show_version_diff("1.2.3", "2.0.0")
        output = string_io.getvalue()

        assert "1.2.3" in output
        assert "2.0.0" in output
        assert "Version Change" in output
    finally:
        release.console = old_console


def test_validate_version_progression_normal():
    """Test validate_version_progression with normal progression."""
    # Should not raise or warn for normal progression
    release.validate_version_progression("1.0.0", "1.0.1", "patch")
    release.validate_version_progression("1.0.0", "1.1.0", "minor")
    release.validate_version_progression("1.0.0", "2.0.0", "major")


def test_validate_version_progression_backwards(capsys):
    """Test validate_version_progression with backwards version."""
    release.validate_version_progression("2.0.0", "1.0.0", "patch")
    captured = capsys.readouterr()
    assert "not greater than old version" in captured.out.lower()


def test_validate_version_progression_wrong_bump_type(capsys):
    """Test validate_version_progression with wrong bump type."""
    release.validate_version_progression("1.0.0", "2.0.0", "patch")
    captured = capsys.readouterr()
    assert "major version changed during patch bump" in captured.out.lower()


def test_validate_version_progression_skipped_versions(capsys):
    """Test validate_version_progression with skipped versions."""
    release.validate_version_progression("1.0.0", "1.0.5", "patch")
    captured = capsys.readouterr()
    assert "skipping versions" in captured.out.lower()


# ============================================================================
# TEST Git Integration Functions (Mocked)
# ============================================================================


def test_run_git_command_success(mocker):
    """Test run_git_command with successful execution."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = Mock(stdout="success output", stderr="", returncode=0)

    success, output = release.run_git_command(["status"], Path("/fake/path"))

    assert success is True
    assert output == "success output"
    mock_run.assert_called_once()


def test_run_git_command_failure(mocker):
    """Test run_git_command with command failure."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = subprocess.CalledProcessError(
        1, ["git"], stderr="error message"
    )

    success, output = release.run_git_command(["status"], Path("/fake/path"))

    assert success is False
    assert output == "error message"


def test_run_git_command_not_found(mocker):
    """Test run_git_command when git is not found."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = FileNotFoundError()

    success, output = release.run_git_command(["status"], Path("/fake/path"))

    assert success is False
    assert output == "git command not found"


def test_git_commit_version_success(mocker, tmp_path, capsys):
    """Test git_commit_version with successful commit."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (True, "M file.txt"),  # status --porcelain
        (True, ""),  # add -u
        (True, "commit successful"),  # commit
    ]

    result = release.git_commit_version(tmp_path, "1.2.3", auto_confirm=True)

    assert result is True
    captured = capsys.readouterr()
    assert "Committed changes" in captured.out


def test_git_commit_version_not_git_repo(mocker, tmp_path, capsys):
    """Test git_commit_version when not in a git repo."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.return_value = (False, "not a git repository")

    result = release.git_commit_version(tmp_path, "1.2.3", auto_confirm=True)

    assert result is False
    captured = capsys.readouterr()
    assert "Not a git repository" in captured.out


def test_git_commit_version_no_changes(mocker, tmp_path, capsys):
    """Test git_commit_version with no changes."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (True, ""),  # status --porcelain (empty = no changes)
    ]

    result = release.git_commit_version(tmp_path, "1.2.3", auto_confirm=True)

    assert result is False
    captured = capsys.readouterr()
    assert "No changes to commit" in captured.out


def test_git_commit_version_user_cancels(mocker, tmp_path, capsys):
    """Test git_commit_version when user cancels."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (True, "M file.txt"),  # status --porcelain
    ]
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    mock_confirm.return_value = False

    result = release.git_commit_version(tmp_path, "1.2.3", auto_confirm=False)

    assert result is False
    captured = capsys.readouterr()
    assert "skipped" in captured.out.lower()


def test_git_tag_version_success(mocker, tmp_path, capsys):
    """Test git_tag_version with successful tag creation."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (False, ""),  # rev-parse v1.2.3 (tag doesn't exist)
        (True, "tag created"),  # tag -a
    ]

    result = release.git_tag_version(tmp_path, "1.2.3", auto_confirm=True)

    assert result is True
    captured = capsys.readouterr()
    # Output may contain ANSI escape codes - strip them before checking
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    clean_output = ansi_escape.sub("", captured.out)
    assert "v1.2.3" in clean_output


def test_git_tag_version_already_exists(mocker, tmp_path, capsys):
    """Test git_tag_version when tag already exists."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (True, "abc123"),  # rev-parse v1.2.3 (tag exists)
    ]

    result = release.git_tag_version(tmp_path, "1.2.3", auto_confirm=True)

    assert result is False
    captured = capsys.readouterr()
    assert "already exists" in captured.out


def test_git_tag_version_user_cancels(mocker, tmp_path):
    """Test git_tag_version when user cancels."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (False, ""),  # rev-parse v1.2.3 (tag doesn't exist)
    ]
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    mock_confirm.return_value = False

    result = release.git_tag_version(tmp_path, "1.2.3", auto_confirm=False)

    assert result is False


# ============================================================================
# TEST CLI Integration
# ============================================================================


def test_cli_check_version_success(project_dir, mocker, capsys):
    """Test CLI --check-version with all files matching."""
    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(project_dir), "--check-version"]
    )

    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "SUCCESS" in captured.out or "1.0.0" in captured.out


def test_cli_check_version_mismatch(tmp_path, mocker, capsys):
    """Test CLI --check-version with version mismatch."""
    (tmp_path / "package.xml").write_text("<version>1.0.0</version>")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "2.0.0"\n')

    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(tmp_path), "--check-version"]
    )

    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 1


def test_cli_check_version_json_output(project_dir, mocker, capsys):
    """Test CLI --check-version with JSON output."""
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--check-version",
            "--output-format",
            "json",
        ],
    )

    with pytest.raises(SystemExit):
        release.main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["consensus_version"] == "1.0.0"
    assert data["consistent"] is True


def test_cli_check_version_short_output(project_dir, mocker, capsys):
    """Test CLI --check-version with --short flag."""
    mocker.patch(
        "sys.argv",
        ["jrl_release.py", "--root", str(project_dir), "--check-version", "--short"],
    )

    with pytest.raises(SystemExit):
        release.main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "1.0.0"


def test_cli_list_files(project_dir, mocker, capsys):
    """Test CLI --list-files."""
    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(project_dir), "--list-files"]
    )

    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "package.xml" in captured.out
    assert "pyproject.toml" in captured.out


def test_cli_list_files_json(project_dir, mocker, capsys):
    """Test CLI --list-files with JSON output."""
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--list-files",
            "--output-format",
            "json",
        ],
    )

    with pytest.raises(SystemExit):
        release.main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert any(f["name"] == "package.xml" for f in data)


def test_cli_update_version(project_dir, mocker, capsys):
    """Test CLI --update-version."""
    mocker.patch(
        "sys.argv",
        ["jrl_release.py", "--root", str(project_dir), "--update-version", "2.3.4"],
    )

    # main() may or may not raise SystemExit depending on the path
    try:
        release.main()
    except SystemExit as e:
        # If it does exit, ensure it's successful
        assert e.code == 0

    # Verify files were updated
    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>2.3.4</version>" in xml_content


def test_cli_update_version_invalid_semver(project_dir, mocker, capsys):
    """Test CLI --update-version with invalid semver."""
    mocker.patch(
        "sys.argv",
        ["jrl_release.py", "--root", str(project_dir), "--update-version", "1.2"],
    )

    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 1


def test_cli_bump_patch(project_dir, mocker, capsys):
    """Test CLI --bump patch."""
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    mock_confirm.return_value = True

    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(project_dir), "--bump", "patch"]
    )

    release.main()

    # Verify version was bumped from 1.0.0 to 1.0.1
    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>1.0.1</version>" in xml_content


def test_cli_bump_minor(project_dir, mocker):
    """Test CLI --bump minor."""
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    mock_confirm.return_value = True

    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(project_dir), "--bump", "minor"]
    )

    release.main()

    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>1.1.0</version>" in xml_content


def test_cli_bump_major(project_dir, mocker):
    """Test CLI --bump major."""
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    mock_confirm.return_value = True

    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(project_dir), "--bump", "major"]
    )

    release.main()

    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>2.0.0</version>" in xml_content


def test_cli_bump_with_auto_confirm(project_dir, mocker):
    """Test CLI --bump with --confirm flag."""
    mocker.patch(
        "sys.argv",
        ["jrl_release.py", "--root", str(project_dir), "--bump", "patch", "--confirm"],
    )

    release.main()

    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>1.0.1</version>" in xml_content


def test_cli_bump_user_cancels(project_dir, mocker, capsys):
    """Test CLI --bump when user cancels."""
    mock_confirm = mocker.patch("rich.prompt.Confirm.ask")
    mock_confirm.return_value = False

    mocker.patch(
        "sys.argv", ["jrl_release.py", "--root", str(project_dir), "--bump", "patch"]
    )

    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 0

    # Version should not be changed
    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>1.0.0</version>" in xml_content


def test_cli_dry_run(project_dir, mocker, capsys):
    """Test CLI --dry-run flag."""
    mocker.patch(
        "sys.argv",
        ["jrl_release.py", "--root", str(project_dir), "--bump", "patch", "--dry-run"],
    )

    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 0

    # Version should not be changed
    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>1.0.0</version>" in xml_content

    captured = capsys.readouterr()
    assert "Dry run" in captured.out


def test_cli_git_commit_and_tag(project_dir, mocker, capsys):
    """Test CLI with --git-commit and --git-tag flags."""
    mock_run = mocker.patch("jrl_release.run_git_command")
    mock_run.side_effect = [
        (True, ""),  # rev-parse --git-dir (commit check)
        (True, "M file.txt"),  # status --porcelain
        (True, ""),  # add -u
        (True, "committed"),  # commit
        (True, ""),  # rev-parse --git-dir (tag check)
        (False, ""),  # rev-parse v1.0.1 (tag doesn't exist)
        (True, "tagged"),  # tag -a
    ]

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--bump",
            "patch",
            "--git-commit",
            "--git-tag",
            "--confirm",
        ],
    )

    release.main()

    captured = capsys.readouterr()
    assert "Committed changes" in captured.out
    assert "Created tag" in captured.out


def test_cli_short_output(project_dir, mocker, capsys):
    """Test CLI with --short flag."""
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "3.2.1",
            "--short",
        ],
    )

    release.main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "3.2.1"


def test_cli_json_output(project_dir, mocker, capsys):
    """Test CLI with --output-format json."""
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "3.2.1",
            "--output-format",
            "json",
        ],
    )

    release.main()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["new_version"] == "3.2.1"
    assert data["previous_version"] is not None  # current version read from files
    assert "updated_files" in data


# ============================================================================
# TEST Helper Functions
# ============================================================================


def test_list_version_files_display(project_dir):
    """Test list_version_files displays table."""
    checks = [
        release.XmlVersionExtractor(project_dir / "package.xml"),
        release.TomlVersionExtractor(
            project_dir / "pyproject.toml", ["project", "version"]
        ),
    ]

    # Capture output using StringIO instead of capsys since function calls sys.exit
    string_io = StringIO()
    test_console = Console(file=string_io)
    old_console = release.console
    release.console = test_console

    try:
        with pytest.raises(SystemExit) as exc_info:
            release.list_version_files(checks)
        assert exc_info.value.code == 0

        output = string_io.getvalue()
        assert "package.xml" in output
        assert "pyproject.toml" in output
    finally:
        release.console = old_console


# ============================================================================
# TEST get_project_name
# ============================================================================


def test_get_project_name_from_cmake(tmp_path):
    """Detects project name from CMakeLists.txt project() command."""
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\nproject(my-awesome-lib VERSION 1.0.0)\n"
    )
    assert release.get_project_name(tmp_path) == "my-awesome-lib"


def test_get_project_name_from_cmake_multiline(tmp_path):
    """Detects project name from a multiline project() command."""
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\nproject(\n  my-lib\n  VERSION 1.0.0\n)\n"
    )
    assert release.get_project_name(tmp_path) == "my-lib"


def test_get_project_name_from_cmake_variable(tmp_path):
    """Detects project name when project() uses a variable defined above."""
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\n"
        'set(PROJECT_NAME_INPUT "my-variable-lib")\n'
        "project(${PROJECT_NAME_INPUT} VERSION 1.0.0)\n"
    )
    assert release.get_project_name(tmp_path) == "my-variable-lib"


def test_get_project_name_from_cmake_nested_variable(tmp_path):
    """Resolves simple chains of variables before project()."""
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\n"
        'set(BASE_NAME "nested-lib")\n'
        'set(PROJECT_NAME_INPUT "${BASE_NAME}")\n'
        "project(${PROJECT_NAME_INPUT} VERSION 1.0.0)\n"
    )
    assert release.get_project_name(tmp_path) == "nested-lib"


def test_get_project_name_prefers_build_dir_cache(tmp_path):
    """A configured build dir is the most reliable project-name source."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "CMakeCache.txt").write_text(
        "//Project name\nCMAKE_PROJECT_NAME:STATIC=cache-project\n",
        encoding="utf-8",
    )
    (tmp_path / "CMakeLists.txt").write_text(
        "project(source-project VERSION 1.0.0)\n",
        encoding="utf-8",
    )
    assert release.get_project_name(tmp_path, build_dir) == "cache-project"


def test_get_project_name_from_cmake_unresolved_variable_falls_back(tmp_path):
    """Falls back to explicit secondary metadata when CMakeLists.txt is unresolved."""
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\n"
        "project(${PROJECT_NAME_INPUT} VERSION 1.0.0)\n"
    )
    (tmp_path / "pixi.toml").write_text(
        '[workspace]\nname = "pixi-fallback"\nversion = "0.1.0"\n'
    )
    assert release.get_project_name(tmp_path) == "pixi-fallback"


def test_get_project_name_from_pixi_toml(tmp_path):
    """Falls back to pixi.toml workspace.name when no CMakeLists.txt exists."""
    (tmp_path / "pixi.toml").write_text(
        '[workspace]\nname = "pixi-project"\nversion = "0.1.0"\n'
    )
    assert release.get_project_name(tmp_path) == "pixi-project"


def test_get_project_name_from_pyproject_toml(tmp_path):
    """Falls back to pyproject.toml project.name when no CMakeLists.txt or pixi.toml exist."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "py-project"\nversion = "0.1.0"\n'
    )
    assert release.get_project_name(tmp_path) == "py-project"


def test_get_project_name_raises_with_clear_message_when_no_sources_exist(tmp_path):
    """Raises a user-facing error instead of guessing from the directory name."""
    with pytest.raises(
        ValueError, match="Could not determine the project name"
    ) as exc_info:
        release.get_project_name(tmp_path)

    error_message = str(exc_info.value)
    assert "CMakeLists.txt: file does not exist" in error_message
    assert "pixi.toml: file does not exist" in error_message
    assert "pyproject.toml: file does not exist" in error_message
    assert "Provide --project-name explicitly" in error_message


# ============================================================================
# TEST _git_ls_files / _git_submodule_paths (mocked)
# ============================================================================


def test_git_ls_files_returns_tracked_files(mocker):
    mocker.patch("shutil.which", return_value="git")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(
        stdout="CMakeLists.txt\nsrc/lib.cpp\n", returncode=0
    )
    files = release._git_ls_files(Path("/fake/repo"))
    assert files == ["CMakeLists.txt", "src/lib.cpp"]


def test_git_submodule_paths_no_gitmodules(tmp_path):
    """Returns empty list when .gitmodules does not exist."""
    assert release._git_submodule_paths(tmp_path) == []


def test_git_submodule_paths_parses_paths(mocker, tmp_path):
    """Parses submodule paths from .gitmodules via git config."""
    (tmp_path / ".gitmodules").write_text("[submodule]\n  path = third_party/eigen\n")
    mocker.patch("shutil.which", return_value="git")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(
        stdout="submodule.third_party/eigen.path third_party/eigen\n",
        returncode=0,
    )
    paths = release._git_submodule_paths(tmp_path)
    assert paths == ["third_party/eigen"]


def test_git_submodule_paths_git_config_fails(mocker, tmp_path):
    """Returns empty list when git config returns non-zero exit code."""
    (tmp_path / ".gitmodules").write_text("[submodule]\n  path = sub\n")
    mocker.patch("shutil.which", return_value="git")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(stdout="", returncode=1)
    assert release._git_submodule_paths(tmp_path) == []


# ============================================================================
# TEST create_dist_tarball (integration with real git repo)
# ============================================================================


def _init_git_repo(repo_dir: Path) -> None:
    """Initialize a git repository with deterministic test identity."""
    subprocess.run(["git", "init", str(repo_dir)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal real git repo with one tracked file."""
    _init_git_repo(tmp_path)
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.22)\nproject(test-project VERSION 1.0.0)\n"
    )
    (tmp_path / "README.md").write_text("# test-project\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path


@pytest.fixture
def minimal_release_project(tmp_path):
    """Create a real minimal project that can complete dist/distcheck/distclean."""
    _init_git_repo(tmp_path)

    repo_root = Path(__file__).resolve().parents[2]
    jrl_modules_dir = (repo_root / "v2" / "modules").as_posix()

    (tmp_path / "README.md").write_text("# mini-release-project\n", encoding="utf-8")
    (tmp_path / "package.xml").write_text(
        """<?xml version=\"1.0\"?>
<package format=\"2\">
  <name>mini-release-project</name>
  <version>1.0.0</version>
  <description>Minimal release test project</description>
</package>
""",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """[project]
name = \"mini-release-project\"
version = \"1.0.0\"
description = \"Minimal release test project\"
""",
        encoding="utf-8",
    )
    (tmp_path / "pixi.toml").write_text(
        """[workspace]
name = \"mini-release-project\"
version = \"1.0.0\"
""",
        encoding="utf-8",
    )
    (tmp_path / "CITATION.cff").write_text(
        """cff-version: 1.2.0
title: \"mini-release-project\"
version: 1.0.0
""",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-01

- Initial release
""",
        encoding="utf-8",
    )
    (tmp_path / "CMakeLists.txt").write_text(
        f"""cmake_minimum_required(VERSION 3.22)
project(mini-release-project VERSION 1.0.0 LANGUAGES NONE)

list(PREPEND CMAKE_MODULE_PATH \"{jrl_modules_dir}\")
include(jrl)

jrl_configure_defaults()
jrl_include_ctest()

add_test(NAME smoke COMMAND ${{CMAKE_COMMAND}} -E true)
install(FILES README.md DESTINATION share/${{PROJECT_NAME}})
""",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path


def test_create_dist_tarball_creates_file(git_repo, tmp_path):
    """create_dist_tarball produces a .tar.gz at the expected path."""
    output_dir = tmp_path / "dist_out"
    tarball = release.create_dist_tarball(git_repo, "test-project", "1.2.3", output_dir)

    assert tarball.exists()
    assert tarball.name == "test-project-1.2.3.tar.gz"


def test_create_dist_tarball_contents(git_repo, tmp_path):
    """Tarball contains tracked files under the versioned prefix."""
    import tarfile as tf

    output_dir = tmp_path / "dist_out"
    tarball = release.create_dist_tarball(git_repo, "test-project", "1.2.3", output_dir)

    with tf.open(str(tarball), "r:gz") as tar:
        names = tar.getnames()

    assert any(n.startswith("test-project-1.2.3/") for n in names)
    assert "test-project-1.2.3/CMakeLists.txt" in names
    assert "test-project-1.2.3/README.md" in names


def test_create_dist_tarball_no_untracked_files(git_repo, tmp_path):
    """Untracked files are NOT included in the tarball."""
    import tarfile as tf

    (git_repo / "untracked.txt").write_text("not tracked")

    output_dir = tmp_path / "dist_out"
    tarball = release.create_dist_tarball(git_repo, "test-project", "1.2.3", output_dir)

    with tf.open(str(tarball), "r:gz") as tar:
        names = tar.getnames()

    assert "test-project-1.2.3/untracked.txt" not in names


def test_create_dist_tarball_rejects_empty_project_name(git_repo, tmp_path):
    """Project names must be explicit and non-empty when creating a tarball."""
    with pytest.raises(ValueError, match="Project name must not be empty"):
        release.create_dist_tarball(git_repo, "   ", "1.2.3", tmp_path / "dist_out")


# ============================================================================
# TEST extract_dist_tarball
# ============================================================================


def test_extract_dist_tarball_roundtrip(git_repo, tmp_path):
    """Extracted directory contains expected files."""
    output_dir = tmp_path / "dist_out"
    tarball = release.create_dist_tarball(git_repo, "test-project", "1.2.3", output_dir)

    extract_dir = tmp_path / "extracted"
    extracted = release.extract_dist_tarball(tarball, extract_dir)

    assert extracted.is_dir()
    assert extracted.name == "test-project-1.2.3"
    assert (extracted / "CMakeLists.txt").exists()
    assert (extracted / "README.md").exists()


def test_extract_dist_tarball_rejects_unsafe_entries(tmp_path):
    """extract_dist_tarball raises ValueError for path-traversal entries."""
    import tarfile as tf

    bad_tarball = tmp_path / "bad.tar.gz"
    with tf.open(str(bad_tarball), "w:gz") as tar:
        info = tf.TarInfo(name="../etc/passwd")
        info.size = 0
        tar.addfile(info)

    with pytest.raises(ValueError, match="Unsafe tarball entry"):
        release.extract_dist_tarball(bad_tarball, tmp_path / "out")


def test_extract_dist_tarball_rejects_unsafe_link_target(tmp_path):
    """Symlink and hardlink targets must stay inside the archive root."""
    import tarfile as tf

    bad_tarball = tmp_path / "bad-link.tar.gz"
    with tf.open(str(bad_tarball), "w:gz") as tar:
        info = tf.TarInfo(name="pkg-1.2.3/link")
        info.type = tf.SYMTYPE
        info.linkname = "../outside"
        tar.addfile(info)

    with pytest.raises(ValueError, match="Unsafe tarball link target"):
        release.extract_dist_tarball(bad_tarball, tmp_path / "out")


def test_extract_dist_tarball_rejects_multiple_top_level_entries(tmp_path):
    """Distributions must unpack into a single versioned directory."""
    import tarfile as tf

    bad_tarball = tmp_path / "bad-layout.tar.gz"
    with tf.open(str(bad_tarball), "w:gz") as tar:
        for name in ["pkg-a/README.md", "pkg-b/README.md"]:
            data = b"doc"
            info = tf.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, BytesIO(data))

    with pytest.raises(ValueError, match="single top-level directory"):
        release.extract_dist_tarball(bad_tarball, tmp_path / "out")


# ============================================================================
# TEST run_cmake_build_target (mocked)
# ============================================================================


def test_run_cmake_build_target_success(mocker, tmp_path):
    mocker.patch("shutil.which", return_value="cmake")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(returncode=0)

    build_dir = tmp_path / "build"
    build_dir.mkdir()

    release.run_cmake_build_target(build_dir, "distcheck")

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "cmake" in args
    assert "--target" in args
    assert "distcheck" in args


def test_run_cmake_build_target_failure(mocker, tmp_path):
    mocker.patch("shutil.which", return_value="cmake")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(returncode=1)

    build_dir = tmp_path / "build"
    build_dir.mkdir()

    with pytest.raises(RuntimeError, match="distcheck"):
        release.run_cmake_build_target(build_dir, "distcheck")


def test_run_cmake_build_target_requires_existing_build_dir():
    with pytest.raises(RuntimeError, match="does not exist"):
        release.run_cmake_build_target(
            Path("/definitely/missing/build-dir"), "distcheck"
        )


def test_run_cmake_configure_success(mocker, tmp_path):
    mocker.patch("shutil.which", return_value="cmake")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = Mock(returncode=0)

    source_dir = tmp_path / "src"
    build_dir = tmp_path / "build"

    release.run_cmake_configure(source_dir, build_dir)

    mock_run.assert_called_once_with(
        ["cmake", "-S", str(source_dir), "-B", str(build_dir)]
    )


def test_run_cmake_configure_failure(mocker, tmp_path):
    mocker.patch("shutil.which", return_value="cmake")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = Mock(returncode=1)

    with pytest.raises(RuntimeError, match="configure failed"):
        release.run_cmake_configure(tmp_path / "src", tmp_path / "build")


# ============================================================================
# TEST CLI -- dist / distcheck / distclean (mocked)
# ============================================================================


def test_cli_dist_requires_build_dir(project_dir, mocker, capsys):
    """--dist without --build-dir exits with error."""
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--dist",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        release.main()
    assert exc_info.value.code == 1


def test_cli_distcheck_requires_build_dir(project_dir, mocker, capsys):
    """--distcheck without --build-dir exits with error."""
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--distcheck",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        release.main()
    assert exc_info.value.code == 1


def test_cli_dist_incompatible_with_check_version(tmp_path, mocker, capsys):
    """--dist is rejected with --check-version."""
    (tmp_path / "package.xml").write_text("<version>1.0.0</version>")
    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(tmp_path),
            "--check-version",
            "--dist",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        release.main()
    assert exc_info.value.code == 1


def test_cli_dist_calls_create_and_extract(project_dir, mocker, tmp_path):
    """--dist invokes create_dist_tarball and extract_dist_tarball."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    mock_create = mocker.patch("jrl_release.create_dist_tarball")
    fake_tarball = tmp_path / "proj-2.0.0.tar.gz"
    fake_tarball.write_bytes(b"")
    mock_create.return_value = fake_tarball

    mock_extract = mocker.patch("jrl_release.extract_dist_tarball")
    mock_extract.return_value = build_dir / "proj-2.0.0"

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_subprocess_run.return_value = mocker.Mock(returncode=0)

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--dist",
            "--build-dir",
            str(build_dir),
            "--project-name",
            "proj",
        ],
    )
    release.main()

    mock_create.assert_called_once_with(project_dir, "proj", "2.0.0", build_dir)
    mock_extract.assert_called_once_with(fake_tarball, build_dir)


def test_cli_distcheck_calls_cmake_build(project_dir, mocker, tmp_path):
    """--distcheck calls run_cmake_build_target with 'distcheck'."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    mocker.patch(
        "jrl_release.create_dist_tarball", return_value=tmp_path / "p-2.0.0.tar.gz"
    )
    mocker.patch("jrl_release.extract_dist_tarball", return_value=build_dir / "p-2.0.0")

    mock_cmake = mocker.patch("jrl_release.run_cmake_build_target")
    mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--dist",
            "--distcheck",
            "--build-dir",
            str(build_dir),
            "--project-name",
            "p",
        ],
    )
    release.main()

    targets = [call.args[1] for call in mock_cmake.call_args_list]
    assert "distcheck" in targets


def test_cli_distclean_calls_cmake_build(project_dir, mocker, tmp_path):
    """--distclean calls run_cmake_build_target with 'distclean'."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    mocker.patch(
        "jrl_release.create_dist_tarball", return_value=tmp_path / "p-2.0.0.tar.gz"
    )
    mocker.patch("jrl_release.extract_dist_tarball", return_value=build_dir / "p-2.0.0")
    mock_cmake = mocker.patch("jrl_release.run_cmake_build_target")
    mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--dist",
            "--distcheck",
            "--distclean",
            "--build-dir",
            str(build_dir),
            "--project-name",
            "p",
        ],
    )
    release.main()

    targets = [call.args[1] for call in mock_cmake.call_args_list]
    assert "distcheck" in targets
    assert "distclean" in targets


def test_cli_distcheck_failure_rolls_back_tag(project_dir, mocker, tmp_path, capsys):
    """When distcheck fails the git tag is deleted."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    mocker.patch(
        "jrl_release.create_dist_tarball", return_value=tmp_path / "p-2.0.0.tar.gz"
    )
    mocker.patch("jrl_release.extract_dist_tarball", return_value=build_dir / "p-2.0.0")
    mocker.patch(
        "jrl_release.run_cmake_build_target",
        side_effect=RuntimeError("distcheck failed"),
    )
    mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))

    mock_git = mocker.patch("jrl_release.run_git_command")
    # rev-parse --git-dir (tag check), rev-parse v2.0.0 (tag not exist), tag -a, tag -d rollback
    mock_git.side_effect = [
        (True, ""),  # rev-parse --git-dir
        (False, ""),  # rev-parse v2.0.0 (doesn't exist)
        (True, ""),  # tag -a v2.0.0
        (True, ""),  # tag -d v2.0.0  (rollback)
    ]

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--dist",
            "--distcheck",
            "--git-tag",
            "--confirm",
            "--build-dir",
            str(build_dir),
            "--project-name",
            "p",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        release.main()

    assert exc_info.value.code == 1
    # Verify tag -d was called
    delete_calls = [
        c
        for c in mock_git.call_args_list
        if c.args[0][0] == "tag" and "-d" in c.args[0]
    ]
    assert len(delete_calls) == 1


def test_cli_dist_dry_run_shows_plan(project_dir, mocker, tmp_path, capsys):
    """--dry-run with --dist shows planned commands without executing them."""
    build_dir = tmp_path / "build"

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(project_dir),
            "--update-version",
            "2.0.0",
            "--dry-run",
            "--dist",
            "--distcheck",
            "--distclean",
            "--build-dir",
            str(build_dir),
            "--project-name",
            "my-proj",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        release.main()
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "distcheck" in captured.out
    assert "distclean" in captured.out
    # Files must NOT be modified
    xml_content = (project_dir / "package.xml").read_text()
    assert "<version>1.0.0</version>" in xml_content


def test_cli_dist_end_to_end_real_project(minimal_release_project, mocker):
    """Run the real release flow with dist, distcheck, and distclean."""
    build_dir = minimal_release_project / "build"
    tarball = build_dir / "mini-release-project-1.0.1.tar.gz"
    extracted_srcdir = build_dir / "mini-release-project-1.0.1"

    mocker.patch(
        "sys.argv",
        [
            "jrl_release.py",
            "--root",
            str(minimal_release_project),
            "--update-version",
            "1.0.1",
            "--dist",
            "--distcheck",
            "--distclean",
            "--build-dir",
            str(build_dir),
            "--project-name",
            "mini-release-project",
            "--confirm",
        ],
    )

    release.main()

    assert tarball.exists()
    assert not extracted_srcdir.exists()
    assert "<version>1.0.1</version>" in (
        minimal_release_project / "package.xml"
    ).read_text(encoding="utf-8")
    assert 'version = "1.0.1"' in (
        minimal_release_project / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert 'version = "1.0.1"' in (minimal_release_project / "pixi.toml").read_text(
        encoding="utf-8"
    )
    assert "## [1.0.1] - " in (minimal_release_project / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"] + sys.argv[1:]))
