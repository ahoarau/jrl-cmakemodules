#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "tomlkit",
#     "ruamel.yaml",
#     "rich",
#     "packaging",
#     "cmake-parser",
# ]
# ///

"""
# jrl_release.py

Version management script for multi-format projects. Keeps version strings in sync across all tracked files and automates the release process.

## Usage

> Requires [`uv`](https://docs.astral.sh/uv/) — it auto-installs dependencies via PEP 723 inline metadata.

```bash
uv run --no-project jrl_release.py [OPTIONS]
```

## Common Commands

```bash
# Check that all files agree on the current version
uv run --no-project jrl_release.py --check-version

# Bump version
uv run --no-project jrl_release.py --bump patch       # 1.0.0 -> 1.0.1
uv run --no-project jrl_release.py --bump minor       # 1.0.0 -> 1.1.0
uv run --no-project jrl_release.py --bump major       # 1.0.0 -> 2.0.0

# Set a specific version
uv run --no-project jrl_release.py --update-version 1.2.3

# Bump, commit and tag in one step
uv run --no-project jrl_release.py --bump patch --git-commit --git-tag
```

## Options

| Option | Description |
| :--- | :--- |
| `--root <PATH>` | Project root (default: cwd). |
| `--bump <major|minor|patch>` | Bump version component. |
| `--update-version <X.Y.Z>` | Set a specific version. |
| `--dry-run` | Show changes without writing files. |
| `--short` | Print only the version string. |
| `--output-format <text|json>` | Output format (default: text). |
| `--confirm` | Skip interactive prompts. |
| `--list-files` | List tracked files. |
| `--git-commit [MSG]` | Commit changes. Optional message (`{version}` placeholder). |
| `--git-tag [NAME]` | Create a tag. Optional name (`{version}` placeholder). |
| `--git-tag-message <MSG>` | Tag annotation (`{version}` placeholder). |
| `--dist` | Create a source tarball after version update. |
| `--distcheck` | Run cmake distcheck target (requires `--build-dir`). |
| `--distclean` | Run cmake distclean target (requires `--build-dir`). |
| `--build-dir <PATH>` | CMake binary directory (required for dist steps). |
| `--project-name <NAME>` | Project name for the tarball (auto-detected if omitted). |

**Git defaults**: commit `chore: bump version to {version}`, tag `v{version}`, tag message `Release version {version}`.

## Supported Files

| File | Key |
| :--- | :--- |
| `package.xml` | `<version>` tag |
| `pyproject.toml` | `project.version` |
| `CHANGELOG.md` | First `## [X.Y.Z]` section (not Unreleased) |
| `pixi.toml` | `[workspace] version` |
| `pixi.lock` | Regenerated via `pixi list` |
| `CITATION.cff` | `version` key |
| `CMakeLists.txt` | `project(... VERSION X.Y.Z ...)` |

> Requires `pixi` CLI if `pixi.lock` exists in the project root.
"""

import sys
import re
import argparse
import datetime
import json
import subprocess
import shutil
import tempfile
import tarfile as tf
from pathlib import Path, PurePosixPath
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict

import tomlkit
import cmake_parser
from ruamel.yaml import YAML
from rich.console import Console
from rich.table import Table
from rich import box
from rich.prompt import Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from packaging.version import parse as parse_version, InvalidVersion

console = Console()

STYLE_INFO = "bold blue"
STYLE_SUCCESS = "green"
STYLE_SUCCESS_STRONG = "bold green"
STYLE_WARNING = "yellow"
STYLE_WARNING_STRONG = "bold yellow"
STYLE_ERROR = "red"
STYLE_ERROR_STRONG = "bold red"
STYLE_MUTED = "dim"
STYLE_OLD_VALUE = "red"
STYLE_NEW_VALUE = "green"
STYLE_UNCHANGED_VALUE = "dim"
STYLE_HIGHLIGHT = "cyan"


class VersionNotPresent(Exception):
    """Raised when a file exists but has no version field configured."""

    pass


class VersionExtractor(ABC):
    def __init__(self, file_path: Path):
        self.file_path = file_path

    @abstractmethod
    def get_version(self) -> str:
        pass

    @abstractmethod
    def update_version(self, new_version: str) -> None:
        pass

    def check_file_exists(self) -> bool:
        return self.file_path.exists()

    @property
    def name(self) -> str:
        return self.file_path.name

    @property
    def path(self) -> str:
        return str(self.file_path)


class XmlVersionExtractor(VersionExtractor):
    def get_version(self) -> str:
        # Simple regex for package.xml to avoid parsing namespaces or losing comments
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r"<version>(.*?)</version>", content)
        if match:
            return match.group(1).strip()
        raise VersionNotPresent(f"No <version> tag found in {self.name}")

    def update_version(self, new_version: str) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace only the first occurrence which is standard for the package version
        new_content = re.sub(
            r"<version>(.*?)</version>",
            f"<version>{new_version}</version>",
            content,
            count=1,
        )

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(new_content)


class TomlVersionExtractor(VersionExtractor):
    def __init__(self, file_path: Path, keys: List[str]):
        super().__init__(file_path)
        self.keys = keys

    def get_version(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = tomlkit.load(f)

        value = data
        for key in self.keys:
            if key in value:
                value = value[key]
            else:
                raise VersionNotPresent(
                    f"Key '{'.'.join(self.keys)}' not found in {self.name}"
                )

        return str(value)

    def update_version(self, new_version: str) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = tomlkit.load(f)

        # Navigate to the key
        container = data
        for key in self.keys[:-1]:
            if key in container:
                container = container[key]
            else:
                raise ValueError(f"Key '{key}' not found in {self.name}")

        container[self.keys[-1]] = new_version

        with open(self.file_path, "w", encoding="utf-8") as f:
            tomlkit.dump(data, f)


class YamlVersionExtractor(VersionExtractor):
    def __init__(self, file_path: Path, keys: List[str]):
        super().__init__(file_path)
        self.keys = keys
        self.yaml = YAML()
        self.yaml.preserve_quotes = True

    def get_version(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = self.yaml.load(f)

        value = data
        for key in self.keys:
            if key in value:
                value = value[key]
            else:
                raise VersionNotPresent(
                    f"Key '{'.'.join(self.keys)}' not found in {self.name}"
                )

        return str(value)

    def update_version(self, new_version: str) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = self.yaml.load(f)

        container = data
        for key in self.keys[:-1]:
            container = container[key]

        container[self.keys[-1]] = new_version

        with open(self.file_path, "w", encoding="utf-8") as f:
            self.yaml.dump(data, f)


class CMakeListsVersionExtractor(VersionExtractor):
    """Specialized extractor for CMakeLists.txt that uses cmake-parser
    and handles both direct VERSION and variables (e.g., from package.xml)."""

    def get_version(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            # Parse the CMakeLists.txt file
            tree = cmake_parser.parse(content)

            fallback_version = None
            project_version = None

            # Walk through all commands
            for node in tree:
                if hasattr(node, "name"):
                    # Look for set(PROJECT_VERSION "...")
                    if node.name.lower() == "set":
                        args = self._get_command_args(node)
                        if len(args) >= 2 and args[0] == "PROJECT_VERSION":
                            # Remove quotes from version string
                            fallback_version = args[1].strip('"')

                    # Look for project(...VERSION ...)
                    elif node.name.lower() == "project":
                        args = self._get_command_args(node)
                        # Find VERSION keyword
                        try:
                            version_idx = args.index("VERSION")
                            if version_idx + 1 < len(args):
                                ver = args[version_idx + 1]
                                # Check if it's a variable reference
                                if not ver.startswith("${"):
                                    project_version = ver
                        except ValueError:
                            pass

            # If project() uses a variable, return fallback
            if fallback_version and not project_version:
                return fallback_version

            # If project() has a literal version, use that
            if project_version:
                return project_version

        except Exception:
            pass  # cmake-parser failed, fall back to regex

        return self._get_version_regex(content)

    def _get_command_args(self, node) -> List[str]:
        """Extract arguments from a cmake command node."""
        args = []
        if hasattr(node, "body"):
            for item in node.body:
                if hasattr(item, "contents"):
                    args.append(item.contents)
        return args

    def _get_version_regex(self, content: str) -> str:
        """Fallback regex-based version extraction."""
        # First try to find set(PROJECT_VERSION "X.Y.Z")
        fallback_pattern = re.compile(
            r'set\s*\(\s*PROJECT_VERSION\s+"([0-9]+\.[0-9]+\.[0-9]+)"',
            re.MULTILINE,
        )
        fallback_match = fallback_pattern.search(content)

        # Also check if project() uses a literal version or variable
        project_pattern = re.compile(
            r"project\s*\([^)]*VERSION\s+([\d.]+|\$\{[^}]+\})", re.MULTILINE
        )
        project_match = project_pattern.search(content)

        # If project() uses a variable, use the fallback version
        if project_match and project_match.group(1).startswith("${"):
            if fallback_match:
                return fallback_match.group(1)
            raise VersionNotPresent(
                f"{self.name} reads version from variable {project_match.group(1)}, no fallback found"
            )

        # If project() uses a literal, return it
        if project_match and not project_match.group(1).startswith("${"):
            return project_match.group(1)

        raise VersionNotPresent(f"No version found in {self.name}")

    def update_version(self, new_version: str) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Update the fallback version in set(PROJECT_VERSION "...")
        fallback_pattern = re.compile(
            r'(set\s*\(\s*PROJECT_VERSION\s+)"([0-9]+\.[0-9]+\.[0-9]+)"',
            re.MULTILINE,
        )

        def repl_fallback(match):
            return f'{match.group(1)}"{new_version}"'

        content = fallback_pattern.sub(repl_fallback, content, count=1)

        # Also update literal version in project() if present
        project_pattern = re.compile(
            r"(project\s*\([^)]*VERSION\s+)([\d.]+)", re.MULTILINE
        )

        def repl_project(match):
            return f"{match.group(1)}{new_version}"

        content = project_pattern.sub(repl_project, content, count=1)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(content)


class ChangelogVersionExtractor(VersionExtractor):
    def __init__(self, file_path: Path, pattern: str = ""):
        super().__init__(file_path)

    def get_version(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for ## [Version]
        matches = re.findall(r"^## \[(.*?)\]", content, re.MULTILINE)
        for version in matches:
            if version.lower() != "unreleased":
                return version
        raise VersionNotPresent(f"No released version found in {self.name}")

    def update_version(self, new_version: str) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        today = datetime.date.today().isoformat()

        pattern = r"^## \[Unreleased\]"
        if not re.search(pattern, content, re.MULTILINE):
            console.print(
                f"[{STYLE_WARNING}]Warning: Could not find '## [Unreleased]' in CHANGELOG.md. Skipping update.[/{STYLE_WARNING}]"
            )
            return

        replacement = f"## [Unreleased]\n\n## [{new_version}] - {today}"

        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        console.print(
            f"[{STYLE_INFO}]Updated CHANGELOG.md header. Note: Link definitions at the bottom were not updated automatically.[/{STYLE_INFO}]"
        )


def validate_semver(version: str) -> str:
    try:
        parsed = parse_version(version)
        if str(parsed) != version.strip():
            raise InvalidVersion(version)
        # Require strict X.Y.Z (no pre/post/dev/local segments)
        if (
            parsed.is_prerelease
            or parsed.is_postrelease
            or parsed.is_devrelease
            or parsed.local
        ):
            raise InvalidVersion(version)
        parts = str(parsed).split(".")
        if len(parts) != 3:
            raise InvalidVersion(version)
        return str(parsed)
    except InvalidVersion:
        raise argparse.ArgumentTypeError(
            f"'{version}' is not a valid Semantic Version."
        )


def parse_semver(version: str) -> Tuple[int, int, int]:
    """Parse a semantic version string into major, minor, patch components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version.strip())
    if not match:
        raise ValueError(f"Invalid semver format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(version: str, bump_type: str) -> str:
    """Bump a semantic version by major, minor, or patch."""
    major, minor, patch = parse_semver(version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def get_current_version(checks: List[VersionExtractor]) -> Optional[str]:
    """Get the current consensus version from all files."""
    versions_found = set()
    errors = []

    for check in checks:
        if check.check_file_exists():
            try:
                version = check.get_version()
                versions_found.add(version)
            except VersionNotPresent:
                pass  # file exists but has no version configured; skip
            except Exception as e:
                errors.append(f"{check.name}: {e}")

    # Report parsing errors
    if errors:
        console.print(
            f"[{STYLE_WARNING}]Warning: Failed to parse version from some files:[/{STYLE_WARNING}]"
        )
        for error in errors:
            console.print(f"  [{STYLE_MUTED}]• {error}[/{STYLE_MUTED}]")

    if len(versions_found) == 1:
        return list(versions_found)[0]
    elif len(versions_found) > 1:
        console.print(
            f"[{STYLE_ERROR}]Error: Multiple versions found: {', '.join(sorted(versions_found))}[/{STYLE_ERROR}]"
        )
        console.print(
            f"[{STYLE_WARNING}]Please run --check-version first to resolve conflicts.[/{STYLE_WARNING}]"
        )
        return None
    else:
        console.print(
            f"[{STYLE_ERROR}]Error: No version found in any files.[/{STYLE_ERROR}]"
        )
        return None


def infer_change_type(
    old_version: str, new_version: str, bump_type: Optional[str] = None
) -> str:
    """Infer change type label (major/minor/patch/custom)."""
    if bump_type in {"major", "minor", "patch"}:
        return bump_type

    try:
        old_major, old_minor, old_patch = parse_semver(old_version)
        new_major, new_minor, new_patch = parse_semver(new_version)
    except ValueError:
        return "custom"

    if new_major != old_major:
        return "major"
    if new_minor != old_minor:
        return "minor"
    if new_patch != old_patch:
        return "patch"
    return "no-change"


def show_version_diff(
    old_version: str, new_version: str, bump_type: Optional[str] = None
) -> None:
    """Display a visual diff between old and new versions."""
    old_parts = old_version.split(".")
    new_parts = new_version.split(".")

    # Build colored versions with highlights on changed parts
    old_colored_parts = []
    new_colored_parts = []

    for old, new in zip(old_parts, new_parts):
        if old != new:
            old_colored_parts.append(f"[{STYLE_OLD_VALUE}]{old}[/{STYLE_OLD_VALUE}]")
            new_colored_parts.append(f"[{STYLE_NEW_VALUE}]{new}[/{STYLE_NEW_VALUE}]")
        else:
            old_colored_parts.append(
                f"[{STYLE_UNCHANGED_VALUE}]{old}[/{STYLE_UNCHANGED_VALUE}]"
            )
            new_colored_parts.append(
                f"[{STYLE_UNCHANGED_VALUE}]{new}[/{STYLE_UNCHANGED_VALUE}]"
            )

    old_colored = ".".join(old_colored_parts)
    new_colored = ".".join(new_colored_parts)

    change_type = infer_change_type(old_version, new_version, bump_type)

    panel = Panel(
        f"[bold]{old_colored} → {new_colored}[/bold]",
        title=f"[{STYLE_WARNING_STRONG}]Version Change ({change_type})[/{STYLE_WARNING_STRONG}]",
        border_style=STYLE_WARNING,
        expand=False,
    )
    console.print(panel)


def validate_version_progression(
    old_version: str, new_version: str, bump_type: str
) -> None:
    """Validate and warn about unusual version progressions."""
    try:
        old_major, old_minor, old_patch = parse_semver(old_version)
        new_major, new_minor, new_patch = parse_semver(new_version)
    except ValueError:
        return  # Can't validate non-semver

    warnings = []

    # Check for skipped versions
    if bump_type == "major":
        if new_major != old_major + 1:
            warnings.append(
                f"Major version jump: {old_major} → {new_major} (skipping versions)"
            )
    elif bump_type == "minor":
        if new_major != old_major:
            warnings.append(
                f"Major version changed during minor bump: {old_major} → {new_major}"
            )
        elif new_minor != old_minor + 1:
            warnings.append(
                f"Minor version jump: {old_minor} → {new_minor} (skipping versions)"
            )
    elif bump_type == "patch":
        if new_major != old_major:
            warnings.append(
                f"Major version changed during patch bump: {old_major} → {new_major}"
            )
        elif new_minor != old_minor:
            warnings.append(
                f"Minor version changed during patch bump: {old_minor} → {new_minor}"
            )
        elif new_patch != old_patch + 1:
            warnings.append(
                f"Patch version jump: {old_patch} → {new_patch} (skipping versions)"
            )

    # Check for backward version
    if (new_major, new_minor, new_patch) <= (old_major, old_minor, old_patch):
        warnings.append("New version is not greater than old version")

    if warnings:
        console.print(
            f"[{STYLE_WARNING_STRONG}]⚠ Version Progression Warnings:[/{STYLE_WARNING_STRONG}]"
        )
        for warning in warnings:
            console.print(f"  [{STYLE_WARNING}]• {warning}[/{STYLE_WARNING}]")
        console.print()


def run_git_command(args: List[str], cwd: Path) -> Tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr or ""
    except FileNotFoundError:
        return False, "git command not found"


def git_commit_version(
    root_dir: Path,
    version: str,
    auto_confirm: bool,
    custom_message: Optional[str] = None,
    files_to_stage: Optional[List[str]] = None,
) -> bool:
    """Commit version changes to git."""
    success, _ = run_git_command(["rev-parse", "--git-dir"], root_dir)
    if not success:
        console.print(
            f"[{STYLE_WARNING}]Not a git repository, skipping git commit.[/{STYLE_WARNING}]"
        )
        return False

    _, status_output = run_git_command(["status", "--porcelain"], root_dir)
    if not status_output:
        console.print(f"[{STYLE_WARNING}]No changes to commit.[/{STYLE_WARNING}]")
        return False

    commit_message = (
        custom_message.format(version=version)
        if custom_message
        else f"chore: bump version to {version}"
    )

    if not auto_confirm:
        confirmed = Confirm.ask(
            f"[bold]Commit changes with message: '{commit_message}'?[/bold]",
            default=True,
        )
        if not confirmed:
            console.print(f"[{STYLE_WARNING}]Git commit skipped.[/{STYLE_WARNING}]")
            return False

    if files_to_stage:
        rel_paths = [str(Path(p).relative_to(root_dir)) for p in files_to_stage]
        console.print(f"[{STYLE_MUTED}]$ git add {' '.join(rel_paths)}[/{STYLE_MUTED}]")
        run_git_command(["add"] + files_to_stage, root_dir)
    else:
        console.print(f"[{STYLE_MUTED}]$ git add -u[/{STYLE_MUTED}]")
        run_git_command(["add", "-u"], root_dir)

    console.print(f"[{STYLE_MUTED}]$ git commit -m '{commit_message}'[/{STYLE_MUTED}]")
    success, output = run_git_command(["commit", "-m", commit_message], root_dir)
    if success:
        console.print(
            f"[{STYLE_SUCCESS}]✓ Committed changes: {commit_message}[/{STYLE_SUCCESS}]"
        )
        return True
    else:
        console.print(f"[{STYLE_ERROR}]Failed to commit: {output}[/{STYLE_ERROR}]")
        return False


def git_tag_version(
    root_dir: Path,
    version: str,
    auto_confirm: bool,
    custom_tag_name: Optional[str] = None,
    custom_tag_message: Optional[str] = None,
) -> bool:
    """Create a git tag for the version."""
    success, _ = run_git_command(["rev-parse", "--git-dir"], root_dir)
    if not success:
        console.print(
            f"[{STYLE_WARNING}]Not a git repository, skipping git tag.[/{STYLE_WARNING}]"
        )
        return False

    tag_name = (
        custom_tag_name.format(version=version) if custom_tag_name else f"v{version}"
    )
    tag_message = (
        custom_tag_message.format(version=version)
        if custom_tag_message
        else f"Release version {version}"
    )

    success, _ = run_git_command(["rev-parse", tag_name], root_dir)
    if success:
        console.print(
            f"[{STYLE_WARNING}]Tag {tag_name} already exists.[/{STYLE_WARNING}]"
        )
        return False

    if not auto_confirm:
        confirmed = Confirm.ask(
            f"[bold]Create git tag '{tag_name}'?[/bold]", default=True
        )
        if not confirmed:
            console.print(f"[{STYLE_WARNING}]Git tag skipped.[/{STYLE_WARNING}]")
            return False

    console.print(
        f"[{STYLE_MUTED}]$ git tag -a {tag_name} -m '{tag_message}'[/{STYLE_MUTED}]"
    )
    success, output = run_git_command(
        ["tag", "-a", tag_name, "-m", tag_message], root_dir
    )
    if success:
        console.print(f"[{STYLE_SUCCESS}]✓ Created tag: {tag_name}[/{STYLE_SUCCESS}]")
        console.print(
            f"[{STYLE_MUTED}]  To push: git push origin {tag_name}[/{STYLE_MUTED}]"
        )
        return True
    else:
        console.print(f"[{STYLE_ERROR}]Failed to create tag: {output}[/{STYLE_ERROR}]")
        return False


def update_pixi_lock(root_dir: Path, dry_run: bool = False) -> Optional[str]:
    """Update pixi.lock file by running 'pixi list'.

    Returns the path to pixi.lock if updated, None otherwise.
    """
    pixi_lock_path = root_dir / "pixi.lock"

    if not pixi_lock_path.exists():
        return None

    if dry_run:
        return None

    console.print(
        f"[{STYLE_INFO}]Running 'pixi list' to update pixi.lock...[/{STYLE_INFO}]"
    )
    try:
        result = subprocess.run(
            ["pixi", "list"],
            cwd=root_dir,
            timeout=60,
        )

        if result.returncode != 0:
            console.print(
                f"[{STYLE_ERROR}]Error: 'pixi list' returned non-zero exit code: {result.returncode}[/{STYLE_ERROR}]"
            )
            console.print(
                f"[{STYLE_ERROR}]Failed to update pixi.lock. Please ensure 'pixi' is installed.[/{STYLE_ERROR}]"
            )
            raise RuntimeError(f"'pixi list' failed with exit code {result.returncode}")

    except subprocess.TimeoutExpired:
        console.print(
            f"[{STYLE_ERROR}]Error: 'pixi list' command timed out[/{STYLE_ERROR}]"
        )
        raise RuntimeError("'pixi list' command timed out after 30 seconds")
    except FileNotFoundError:
        console.print(f"[{STYLE_ERROR}]Error: 'pixi' command not found[/{STYLE_ERROR}]")
        console.print(
            f"[{STYLE_ERROR}]pixi.lock exists but 'pixi' executable is not available.[/{STYLE_ERROR}]"
        )
        console.print(
            f"[{STYLE_INFO}]Please install pixi: https://pixi.sh[/{STYLE_INFO}]"
        )
        raise RuntimeError("'pixi' executable not found. Install from https://pixi.sh")
    except Exception as e:
        console.print(
            f"[{STYLE_ERROR}]Error: Failed to run 'pixi list': {e}[/{STYLE_ERROR}]"
        )
        raise RuntimeError(f"Failed to run 'pixi list': {e}") from e

    console.print(
        f"[{STYLE_SUCCESS}]✓ Updated pixi.lock via 'pixi list'[/{STYLE_SUCCESS}]"
    )

    return str(pixi_lock_path)


def _require_command(command_name: str) -> str:
    command_path = shutil.which(command_name)
    if command_path is None:
        raise RuntimeError(f"Required command '{command_name}' was not found in PATH.")
    return command_path


def _validate_archive_path(path_value: str, label: str) -> PurePosixPath:
    if not path_value:
        raise ValueError(f"Unsafe tarball {label}: empty path is not allowed.")
    if "\\" in path_value:
        raise ValueError(
            f"Unsafe tarball {label}: backslashes are not allowed: {path_value}"
        )
    if re.match(r"^[A-Za-z]:", path_value):
        raise ValueError(
            f"Unsafe tarball {label}: drive-qualified paths are not allowed: {path_value}"
        )

    pure_path = PurePosixPath(path_value)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(f"Unsafe tarball {label}: {path_value}")
    return pure_path


def _strip_cmake_quotes(value: str) -> str:
    """Remove matching single or double quotes around a CMake token."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_cmake_elements(content: str) -> List[object]:
    """Parse CMake content into AST elements."""
    return list(cmake_parser.parse_tree(content))


def _get_cmake_command_name(node) -> Optional[str]:
    """Return a normalized command name from a cmake-parser node."""
    # Generic Command nodes expose .identifier; typed nodes (Set, If, …) use the class name
    command_name = getattr(node, "identifier", None)
    if command_name is None:
        node_type_name = type(node).__name__
        if node_type_name != "Command":
            command_name = node_type_name
    if command_name is None:
        return None
    return str(command_name).lower()


def _get_cmake_command_args(node) -> List[str]:
    """Extract raw argument values from a cmake-parser command node."""
    args = []
    for item in getattr(node, "args", []):
        token_value = getattr(item, "value", None)
        if token_value is not None:
            args.append(str(token_value))
    return args


def _resolve_cmake_variable_token(
    token: str, variables: Dict[str, str], max_depth: int = 10
) -> Optional[str]:
    """Resolve a simple ``${VAR}`` token using variables defined earlier."""
    resolved = _strip_cmake_quotes(token).strip()
    for _ in range(max_depth):
        match = re.fullmatch(r"\$\{([^}]+)\}", resolved)
        if not match:
            return resolved or None
        variable_name = match.group(1)
        if variable_name not in variables:
            return None
        resolved = _strip_cmake_quotes(variables[variable_name]).strip()
    return None


def _get_project_name_from_cmake(cmake_lists: Path) -> str:
    """Detect project name from CMakeLists.txt using cmake-parser only."""
    content = cmake_lists.read_text(encoding="utf-8")
    variables: Dict[str, str] = {}

    for node in _parse_cmake_elements(content):
        command_name = _get_cmake_command_name(node)
        if not command_name:
            continue

        args = _get_cmake_command_args(node)
        if not args:
            continue

        if command_name == "set":
            if len(args) >= 2:
                var_name = _strip_cmake_quotes(args[0]).strip()
                if var_name:
                    variables[var_name] = args[1]
            continue

        if command_name == "project":
            project_name = _resolve_cmake_variable_token(args[0], variables)
            if project_name:
                return project_name
            raise ValueError(
                "CMakeLists.txt contains a project() call, but its first argument "
                "could not be resolved. Only literal names and simple ${VAR} references "
                "defined earlier with set(VAR value) are supported."
            )

    raise ValueError(
        "CMakeLists.txt does not contain a readable project() declaration."
    )


def _get_project_name_from_build_dir(build_dir: Path) -> str:
    """Read the configured project name from a populated CMake build directory."""
    cmake_cache = build_dir / "CMakeCache.txt"
    if not cmake_cache.exists():
        raise ValueError(f"{cmake_cache} does not exist.")

    for line in cmake_cache.read_text(encoding="utf-8").splitlines():
        if line.startswith("CMAKE_PROJECT_NAME:"):
            _, _, value = line.partition("=")
            project_name = value.strip()
            if project_name:
                return project_name
            raise ValueError(
                f"{cmake_cache} contains an empty CMAKE_PROJECT_NAME entry."
            )

    raise ValueError(f"{cmake_cache} does not define CMAKE_PROJECT_NAME.")


def _get_project_name_from_pixi_toml(pixi_toml: Path) -> str:
    """Read project name from pixi.toml [workspace].name."""
    with open(pixi_toml, "r", encoding="utf-8") as f:
        data = tomlkit.load(f)
    if "workspace" not in data or "name" not in data["workspace"]:
        raise ValueError("pixi.toml does not define [workspace].name.")
    project_name = str(data["workspace"]["name"]).strip()
    if not project_name:
        raise ValueError("pixi.toml defines an empty [workspace].name.")
    return project_name


def _get_project_name_from_pyproject_toml(pyproject_toml: Path) -> str:
    """Read project name from pyproject.toml [project].name."""
    with open(pyproject_toml, "r", encoding="utf-8") as f:
        data = tomlkit.load(f)
    if "project" not in data or "name" not in data["project"]:
        raise ValueError("pyproject.toml does not define [project].name.")
    project_name = str(data["project"]["name"]).strip()
    if not project_name:
        raise ValueError("pyproject.toml defines an empty [project].name.")
    return project_name


def get_project_name(root_dir: Path, build_dir: Optional[Path] = None) -> str:
    """Determine the project name from explicit project metadata.

    Tries in order:
    1. ``CMAKE_PROJECT_NAME`` from ``<build_dir>/CMakeCache.txt`` (if build_dir given)
    2. ``project(<name> ...)`` in CMakeLists.txt
    3. ``[workspace] name`` in pixi.toml
    4. ``[project] name`` in pyproject.toml
    """
    errors: List[str] = []
    source_probes: List[Tuple[str, object]] = []

    if build_dir is not None:
        source_probes.append(
            (
                f"build dir {build_dir}",
                lambda: _get_project_name_from_build_dir(build_dir),
            )
        )

    def _load(path: Path, reader):
        if not path.exists():
            raise ValueError("file does not exist.")
        return reader(path)

    source_probes.extend(
        [
            (
                "CMakeLists.txt",
                lambda: _load(
                    root_dir / "CMakeLists.txt", _get_project_name_from_cmake
                ),
            ),
            (
                "pixi.toml",
                lambda: _load(root_dir / "pixi.toml", _get_project_name_from_pixi_toml),
            ),
            (
                "pyproject.toml",
                lambda: _load(
                    root_dir / "pyproject.toml", _get_project_name_from_pyproject_toml
                ),
            ),
        ]
    )

    for source_label, probe in source_probes:
        try:
            return probe()
        except (OSError, ValueError) as exc:
            errors.append(f"{source_label}: {exc}")

    details = "\n".join(f"- {e}" for e in errors)
    raise ValueError(
        "Could not determine the project name from explicit metadata.\n"
        "Tried the following sources:\n"
        f"{details}\n"
        "Provide --project-name explicitly, or configure the project so one of these sources is available."
    )


def _git_ls_files(repo_dir: Path) -> List[str]:
    """Return the list of tracked files in *repo_dir* via ``git ls-files``."""
    result = subprocess.run(
        [
            _require_command("git"),
            "ls-files",
            "--cached",
            "--full-name",
            "--no-empty-directory",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def _git_submodule_paths(repo_dir: Path) -> List[str]:
    """Return relative submodule paths declared in *repo_dir*/.gitmodules."""
    if not (repo_dir / ".gitmodules").exists():
        return []
    result = subprocess.run(
        [
            _require_command("git"),
            "config",
            "--file",
            ".gitmodules",
            "--get-regexp",
            r"submodule\..*\.path",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    paths = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            paths.append(parts[1].strip())
    return paths


def _add_repo_to_tar(tar, repo_dir: Path, prefix: str, rel_base: str = "") -> None:
    """Recursively add all tracked files (and submodules) to an open tarfile."""
    import os

    for rel_path in _git_ls_files(repo_dir):
        abs_path = repo_dir / rel_path
        arcname = prefix + (rel_base + "/" if rel_base else "") + rel_path
        if abs_path.is_symlink():
            info = tf.TarInfo(name=arcname)
            info.type = tf.SYMTYPE
            info.linkname = os.readlink(str(abs_path))
            tar.addfile(info)
        elif abs_path.is_file():
            tar.add(str(abs_path), arcname=arcname)

    for sub_path in _git_submodule_paths(repo_dir):
        sub_dir = repo_dir / sub_path
        if sub_dir.is_dir():
            sub_rel = (rel_base + "/" if rel_base else "") + sub_path
            _add_repo_to_tar(tar, sub_dir, prefix, sub_rel)


def create_dist_tarball(
    source_dir: Path,
    project_name: str,
    version: str,
    output_dir: Path,
) -> Path:
    """Create a ``<project_name>-<version>.tar.gz`` source tarball.

    Uses ``git ls-files`` to collect tracked files and recurses into submodules
    via ``.gitmodules``.

    Returns the path to the created tarball.
    """
    if not source_dir.is_dir():
        raise RuntimeError(f"Source directory does not exist: {source_dir}")
    if not project_name.strip():
        raise ValueError("Project name must not be empty.")

    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{project_name}-{version}/"
    tarball_path = output_dir / f"{project_name}-{version}.tar.gz"

    console.print(
        f"[{STYLE_INFO}]Creating source tarball {tarball_path.name}...[/{STYLE_INFO}]"
    )

    with tf.open(str(tarball_path), "w:gz") as tar:
        _add_repo_to_tar(tar, source_dir, prefix)

    size_kb = tarball_path.stat().st_size // 1024
    console.print(
        f"[{STYLE_SUCCESS}]✓ Created {tarball_path.name} ({size_kb} KB)[/{STYLE_SUCCESS}]"
    )
    return tarball_path


def extract_dist_tarball(tarball_path: Path, dest_dir: Path) -> Path:
    """Extract *tarball_path* into *dest_dir* and return the top-level extracted directory.

    Raises ``ValueError`` for unsafe entries (absolute paths or ``..`` components).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    with tf.open(str(tarball_path), "r:gz") as tar:
        members = tar.getmembers()
        if not members:
            raise ValueError("Tarball is empty.")

        top_dirs: set = set()
        for member in members:
            member_path = _validate_archive_path(member.name, "entry")
            if not member_path.parts:
                raise ValueError(f"Unsafe tarball entry: {member.name}")
            top_dirs.add(member_path.parts[0])
            if member.issym() or member.islnk():
                _validate_archive_path(
                    member.linkname, f"link target for {member.name}"
                )

        for member in members:
            tar.extract(member, str(dest_dir))

    if len(top_dirs) != 1:
        raise ValueError(
            f"Expected a single top-level directory in the tarball, got: {top_dirs}"
        )
    extracted = dest_dir / next(iter(top_dirs))
    if not extracted.is_dir():
        raise ValueError(
            f"Expected extracted top-level directory to exist, got: {extracted}"
        )
    console.print(f"[{STYLE_SUCCESS}]✓ Extracted to {extracted}[/{STYLE_SUCCESS}]")
    return extracted


def run_cmake_configure(source_dir: Path, build_dir: Path) -> None:
    """Run ``cmake -S <source_dir> -B <build_dir>`` with actionable errors."""
    cmake_command = _require_command("cmake")
    cmd = [cmake_command, "-S", str(source_dir), "-B", str(build_dir)]
    console.print(f"[{STYLE_MUTED}]$ {' '.join(cmd)}[/{STYLE_MUTED}]")
    try:
        result = subprocess.run(cmd)
    except OSError as exc:
        raise RuntimeError(f"Failed to run cmake configure command: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"cmake configure failed for build directory {build_dir} (exit code {result.returncode})"
        )


def run_cmake_build_target(build_dir: Path, target: str) -> None:
    """Run ``cmake --build <build_dir> --target <target>``.

    Raises ``RuntimeError`` on non-zero exit.
    """
    if not build_dir.is_dir():
        raise RuntimeError(f"CMake build directory does not exist: {build_dir}")

    cmake_command = _require_command("cmake")
    cmd = [cmake_command, "--build", str(build_dir), "--target", target]
    console.print(f"[{STYLE_MUTED}]$ {' '.join(cmd)}[/{STYLE_MUTED}]")
    try:
        result = subprocess.run(cmd)
    except OSError as exc:
        raise RuntimeError(f"Failed to run cmake build command: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"cmake --build --target {target} failed (exit code {result.returncode})"
        )


def create_backups(file_paths: List[Path]) -> Dict[Path, Path]:
    """Create backup copies of files in a temporary directory.

    Returns a mapping of original paths to backup paths.
    """
    backups = {}
    temp_dir = Path(tempfile.mkdtemp(prefix="release_backup_"))

    for file_path in file_paths:
        if file_path.exists():
            backup_path = temp_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            backups[file_path] = backup_path

    return backups


def restore_backups(backups: Dict[Path, Path]) -> None:
    """Restore files from backups and cleanup temporary directory."""
    if not backups:
        return

    # Get temp directory from first backup
    temp_dir = None
    for original_path, backup_path in backups.items():
        if backup_path.exists():
            shutil.copy2(backup_path, original_path)
            temp_dir = backup_path.parent

    # Clean up temp directory
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir)


def cleanup_backups(backups: Dict[Path, Path]) -> None:
    """Remove backup files without restoring."""
    if not backups:
        return

    # Get temp directory from first backup
    temp_dir = None
    for backup_path in backups.values():
        temp_dir = backup_path.parent
        break

    # Clean up temp directory
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir)


def list_version_files(checks: List[VersionExtractor]) -> None:
    """List all files that are checked for versions."""
    table = Table(title="Version Files", box=box.ROUNDED)
    table.add_column("File", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Exists", justify="center")
    table.add_column("Type", style="magenta")

    for check in checks:
        exists = (
            f"[{STYLE_SUCCESS}]✓[/{STYLE_SUCCESS}]"
            if check.check_file_exists()
            else f"[{STYLE_ERROR}]✗[/{STYLE_ERROR}]"
        )
        file_type = check.__class__.__name__.replace("VersionExtractor", "")
        table.add_row(check.name, str(check.file_path), exists, file_type)

    console.print(table)
    sys.exit(0)


def handle_check_version(checks: List[VersionExtractor], args) -> int:
    """Handle the --check-version command.

    Returns the exit code.
    """
    results = []
    versions_found = set()
    errors = False

    if not args.short:
        console.print(
            f"[{STYLE_INFO}]Checking versions in {args.root}...[/{STYLE_INFO}]"
        )

    for check in checks:
        result = {
            "file": check.name,
            "version": None,
            "status": "Unknown",
            "message": "",
        }

        if not check.check_file_exists():
            result["status"] = "Missing"
            result["message"] = "File not found"
        else:
            try:
                version = check.get_version()
                result["version"] = version
                result["status"] = "Found"
                versions_found.add(version)
            except VersionNotPresent as e:
                result["status"] = "Warning"
                result["message"] = str(e)
            except Exception as e:
                result["status"] = "Error"
                result["message"] = str(e)
                errors = True

        results.append(result)

    consensus_version = None
    if len(versions_found) == 1:
        consensus_version = list(versions_found)[0]
    elif len(versions_found) > 1:
        errors = True
        consensus_version = "MISMATCH"

    if args.output_format == "json":
        out_payload = {
            "consensus_version": consensus_version,
            "files": results,
            "consistent": not errors and len(versions_found) == 1,
        }
        print(json.dumps(out_payload, indent=2))
        return 1 if errors else 0

    # Standard Rich table output
    table = Table(title="Version Check Summary", box=box.ROUNDED)
    table.add_column("File", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for res in results:
        status_style = res["status"]
        if res["status"] == "Found":
            status_style = f"[{STYLE_SUCCESS}]Found[/{STYLE_SUCCESS}]"
        elif res["status"] == "Missing":
            status_style = f"[{STYLE_WARNING}]Missing[/{STYLE_WARNING}]"
        elif res["status"] == "Warning":
            status_style = f"[{STYLE_WARNING}]Warning[/{STYLE_WARNING}]"
        elif res["status"] == "Error":
            status_style = f"[{STYLE_ERROR}]Error[/{STYLE_ERROR}]"

        version_display = res["version"] if res["version"] else "-"
        if res["version"]:
            if (
                consensus_version
                and consensus_version != "MISMATCH"
                and res["version"] == consensus_version
            ):
                version_display = f"[{STYLE_SUCCESS}]{res['version']}[/{STYLE_SUCCESS}]"
            elif consensus_version == "MISMATCH":
                version_display = f"[{STYLE_WARNING}]{res['version']}[/{STYLE_WARNING}]"

        table.add_row(res["file"], version_display, status_style, res["message"])

    if not args.short:
        console.print(table)

    if args.short and consensus_version and consensus_version != "MISMATCH":
        print(consensus_version)

    if errors:
        if len(versions_found) > 1:
            console.print(
                f"\n[{STYLE_ERROR_STRONG}]FAILURE:[/{STYLE_ERROR_STRONG}] Found conflicting versions: {', '.join(sorted(versions_found))}"
            )
        else:
            console.print(
                f"\n[{STYLE_ERROR_STRONG}]FAILURE:[/{STYLE_ERROR_STRONG}] Errors encountered (parsing errors)."
            )
        return 1
    elif not versions_found:
        console.print(
            f"\n[{STYLE_ERROR_STRONG}]FAILURE:[/{STYLE_ERROR_STRONG}] No version files found in {args.root}."
        )
        return 1
    else:
        if not args.short:
            console.print(
                f"\n[{STYLE_SUCCESS_STRONG}]SUCCESS:[/{STYLE_SUCCESS_STRONG}] All files match version [{STYLE_SUCCESS}]{consensus_version}[/{STYLE_SUCCESS}]."
            )
        return 0


def perform_version_updates(
    checks: List[VersionExtractor],
    target_version: str,
    dry_run: bool = False,
) -> Tuple[List[str], List[str], bool, List[Tuple[str, str, str]]]:
    """Apply version updates to all files.

    Returns: (updated_files, updated_file_paths, failed, dry_run_rows)
    dry_run_rows contains (name, old_version, new_version) tuples when dry_run=True.
    """
    updated_files = []
    updated_file_paths = []
    failed = False
    dry_run_rows: List[Tuple[str, str, str]] = []

    for check in checks:
        if check.check_file_exists():
            try:
                if dry_run:
                    curr = check.get_version()
                    dry_run_rows.append((check.name, curr, target_version))
                else:
                    try:
                        old_version = check.get_version()
                    except VersionNotPresent:
                        continue
                    except Exception:
                        old_version = "?"
                    check.update_version(target_version)
                    dry_run_rows.append((check.name, old_version, target_version))
                    line = Text()
                    line.append(f"  {check.name:<22}", style="cyan")
                    line.append(old_version, style=STYLE_OLD_VALUE)
                    line.append("  →  ", style="dim")
                    line.append(target_version, style=STYLE_NEW_VALUE)
                    console.print(line)
                updated_files.append(check.name)
                updated_file_paths.append(str(check.file_path))
            except VersionNotPresent:
                pass  # file exists but has no version configured; skip
            except Exception as e:
                console.print(
                    f"[{STYLE_ERROR}]Failed to update {check.name}: {e}[/{STYLE_ERROR}]"
                )
                if not dry_run:
                    failed = True

    return updated_files, updated_file_paths, failed, dry_run_rows


def show_dry_run_panel(
    dry_run_rows: List[Tuple[str, str, str]],
    pixi_lock_would_update: bool,
    git_lines: List[str],
) -> None:
    """Display a unified dry-run preview."""
    console.print(
        f"\n[{STYLE_WARNING_STRONG}]Dry run — no files were modified[/{STYLE_WARNING_STRONG}]"
    )
    console.print()

    console.print("  [bold cyan]Files[/bold cyan]")
    console.print(f"  [dim]{'─' * 44}[/dim]")
    for name, old, new in dry_run_rows:
        line = Text()
        line.append(f"  {name:<22}", style="cyan")
        line.append(old, style=STYLE_OLD_VALUE)
        line.append("  →  ", style="dim")
        line.append(new, style=STYLE_NEW_VALUE)
        console.print(line)
    if pixi_lock_would_update:
        line = Text()
        line.append(f"  {'pixi.lock':<22}", style="cyan")
        line.append("regenerated via pixi list", style="dim")
        console.print(line)

    if git_lines:
        console.print()
        console.print("  [bold cyan]Git[/bold cyan]")
        console.print(f"  [dim]{'─' * 44}[/dim]")
        for cmd in git_lines:
            console.print(f"  [{STYLE_MUTED}]{cmd}[/{STYLE_MUTED}]", highlight=False)
    console.print()


def show_result_panel(
    pixi_lock_updated: bool,
) -> None:
    """Display a polished summary of completed version updates."""
    if pixi_lock_updated:
        line = Text()
        line.append(f"  {'pixi.lock':<22}", style="cyan")
        line.append("regenerated via pixi list", style="dim")
        console.print(line)
    console.print()
    console.print(
        f"[{STYLE_SUCCESS_STRONG}]✓ Version updated successfully[/{STYLE_SUCCESS_STRONG}]"
    )


class RichHelpAction(argparse.Action):
    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None,
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        if parser.description:
            console.print(Markdown(parser.description))

        # Print the standard argparse usage and options
        # We clear the description to avoid printing the markdown source again
        original_description = parser.description
        parser.description = None

        console.print(Text("\nCommand Reference:\n", style="bold"))
        console.print(Text(parser.format_help()))

        parser.description = original_description
        parser.exit()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action=RichHelpAction,
        help="Show this help message and exit",
    )
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="Project root directory"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Auto-confirm all actions without prompting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files.",
    )
    parser.add_argument(
        "--git-commit",
        nargs="?",
        const=True,
        default=None,
        metavar="MESSAGE",
        help="Commit version changes to git. Optionally provide a custom commit message. Use {version} as placeholder. Default: 'chore: bump version to {version}'",
    )
    parser.add_argument(
        "--git-tag",
        nargs="?",
        const=True,
        default=None,
        metavar="NAME",
        help="Create a git tag for the new version. Optionally provide a custom tag name. Use {version} as placeholder. Default: 'v{version}'",
    )
    parser.add_argument(
        "--git-tag-message",
        type=str,
        default=None,
        metavar="MESSAGE",
        help="Custom git tag message. Use {version} as placeholder for version number. Default: 'Release version {version}'",
    )
    parser.add_argument(
        "--dist",
        action="store_true",
        help="Create a source tarball after version update.",
    )
    parser.add_argument(
        "--distcheck",
        action="store_true",
        help="Run cmake --build --target distcheck after --dist (requires --build-dir).",
    )
    parser.add_argument(
        "--distclean",
        action="store_true",
        help="Run cmake --build --target distclean after --distcheck (requires --build-dir).",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=None,
        metavar="PATH",
        help="CMake binary directory. Required for --dist, --distcheck, --distclean.",
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default=None,
        metavar="NAME",
        help="Project name for the tarball. Auto-detected from CMakeLists.txt / pixi.toml / pyproject.toml if not provided.",
    )
    parser.add_argument(
        "--short",
        action="store_true",
        help="Output only the final version string.",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check-version", action="store_true", help="Check versions across files."
    )
    group.add_argument(
        "--list-files",
        action="store_true",
        help="List all files that are checked for versions.",
    )
    group.add_argument(
        "--update-version",
        type=str,
        help="Update version in all files (enforces semver).",
    )
    group.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Bump the project version.",
    )

    args = parser.parse_args()
    root_dir = args.root

    # Redirect console output to stderr for clean stdout with json/short
    global console
    if args.short or args.output_format == "json":
        console = Console(file=sys.stderr)
    else:
        console = Console()

    if (args.dist or args.distcheck or args.distclean) and (
        args.check_version or args.list_files
    ):
        console.print(
            f"[{STYLE_ERROR}]--dist, --distcheck, --distclean are only valid with --bump or --update-version.[/{STYLE_ERROR}]"
        )
        sys.exit(1)

    if args.update_version:
        try:
            if not re.match(r"^\d+\.\d+\.\d+$", args.update_version):
                console.print(
                    f"[{STYLE_ERROR}]Invalid SemVer '{args.update_version}'. strict X.Y.Z required.[/{STYLE_ERROR}]"
                )
                sys.exit(1)
        except Exception as e:
            console.print(
                f"[{STYLE_ERROR}]Error validating version: {e}[/{STYLE_ERROR}]"
            )
            sys.exit(1)

    checks: List[VersionExtractor] = [
        XmlVersionExtractor(root_dir / "package.xml"),
        TomlVersionExtractor(root_dir / "pyproject.toml", ["project", "version"]),
        ChangelogVersionExtractor(root_dir / "CHANGELOG.md", r""),
        TomlVersionExtractor(root_dir / "pixi.toml", ["workspace", "version"]),
        YamlVersionExtractor(root_dir / "CITATION.cff", ["version"]),
        CMakeListsVersionExtractor(root_dir / "CMakeLists.txt"),
    ]

    if args.list_files:
        if args.output_format == "json":
            files_list = []
            for check in checks:
                files_list.append(
                    {
                        "name": check.name,
                        "path": str(check.file_path),
                        "exists": check.check_file_exists(),
                        "type": check.__class__.__name__.replace(
                            "VersionExtractor", ""
                        ),
                    }
                )
            print(json.dumps(files_list, indent=2))
        else:
            list_version_files(checks)
        sys.exit(0)

    if args.check_version:
        sys.exit(handle_check_version(checks, args))

    current_version = None
    new_version_str = None

    if args.update_version:
        new_version_str = args.update_version
        current_version = get_current_version(checks)
        if not args.dry_run:
            console.print(
                f"[{STYLE_INFO}]Updating versions to {new_version_str} in {root_dir}...[/{STYLE_INFO}]"
            )
    elif args.bump:
        current_version = get_current_version(checks)
        if not current_version:
            sys.exit(1)

        try:
            new_version_str = bump_version(current_version, args.bump)
        except ValueError as e:
            console.print(f"[{STYLE_ERROR}]Error: {e}[/{STYLE_ERROR}]")
            sys.exit(1)

        show_version_diff(current_version, new_version_str, args.bump)
        validate_version_progression(current_version, new_version_str, args.bump)

        if args.dry_run:
            confirmed = True
        elif args.confirm:
            confirmed = True
        else:
            confirmed = Confirm.ask(
                f"\n[bold]Do you want to upgrade from [{STYLE_INFO}]{current_version}[/{STYLE_INFO}] to [{STYLE_NEW_VALUE}]{new_version_str}[/{STYLE_NEW_VALUE}]?[/bold]",
                default=True,
            )

        if not confirmed:
            console.print(f"[{STYLE_WARNING}]Upgrade cancelled.[/{STYLE_WARNING}]")
            sys.exit(0)

    if new_version_str is None:
        console.print(
            f"[{STYLE_ERROR}]Internal error: target version is undefined.[/{STYLE_ERROR}]"
        )
        sys.exit(1)
    target_version: str = new_version_str

    backups = {}
    if not args.dry_run:
        file_paths_to_backup = [
            check.file_path for check in checks if check.check_file_exists()
        ]
        backups = create_backups(file_paths_to_backup)
        console.print(
            f"[{STYLE_MUTED}]Created backups for {len(backups)} files[/{STYLE_MUTED}]"
        )

    try:
        if not args.dry_run and args.output_format == "text":
            console.print()
            console.print("  [bold cyan]Files[/bold cyan]")
            console.print(f"  [dim]{'─' * 44}[/dim]")
        updated_files, updated_file_paths, failed, dry_run_rows = (
            perform_version_updates(checks, target_version, args.dry_run)
        )

        if failed:
            if backups:
                console.print(
                    f"[{STYLE_WARNING}]Restoring files from backup due to failures...[/{STYLE_WARNING}]"
                )
                restore_backups(backups)
                console.print(
                    f"[{STYLE_SUCCESS}]Files restored from backup[/{STYLE_SUCCESS}]"
                )
            sys.exit(1)

        try:
            pixi_lock_path = update_pixi_lock(root_dir, args.dry_run)
            if pixi_lock_path:
                updated_files.append("pixi.lock")
                updated_file_paths.append(pixi_lock_path)
        except RuntimeError as e:
            console.print(
                f"[{STYLE_ERROR}]Pixi lock update failed: {e}[/{STYLE_ERROR}]"
            )
            if backups:
                console.print(
                    f"[{STYLE_WARNING}]Restoring files from backup...[/{STYLE_WARNING}]"
                )
                restore_backups(backups)
                console.print(
                    f"[{STYLE_SUCCESS}]Files restored from backup[/{STYLE_SUCCESS}]"
                )
            sys.exit(1)

        if backups:
            cleanup_backups(backups)
    except Exception as e:
        console.print(f"[{STYLE_ERROR}]Unexpected error: {e}[/{STYLE_ERROR}]")
        if backups:
            console.print(
                f"[{STYLE_WARNING}]Restoring files from backup...[/{STYLE_WARNING}]"
            )
            restore_backups(backups)
            console.print(
                f"[{STYLE_SUCCESS}]Files restored from backup[/{STYLE_SUCCESS}]"
            )
        raise

    if args.output_format == "json":
        res_json = {
            "previous_version": current_version,
            "new_version": target_version,
            "updated_files": updated_files,
            "dry_run": args.dry_run,
        }
        print(json.dumps(res_json, indent=2))

    elif args.short:
        print(target_version)

    if args.dry_run:
        pixi_lock_would_update = (root_dir / "pixi.lock").exists()

        git_lines: List[str] = []
        if args.git_commit is not None:
            custom_message = None if args.git_commit is True else args.git_commit
            commit_message = (
                custom_message.format(version=target_version)
                if custom_message
                else f"chore: bump version to {target_version}"
            )
            rel_paths = (
                [str(Path(p).relative_to(root_dir)) for p in updated_file_paths]
                if updated_file_paths
                else None
            )
            git_lines.append(f"$ git add {' '.join(rel_paths) if rel_paths else '-u'}")
            git_lines.append(f"$ git commit -m '{commit_message}'")
        if args.git_tag is not None:
            custom_tag_name = None if args.git_tag is True else args.git_tag
            tag_name = (
                custom_tag_name.format(version=target_version)
                if custom_tag_name
                else f"v{target_version}"
            )
            tag_message = (
                args.git_tag_message.format(version=target_version)
                if args.git_tag_message
                else f"Release version {target_version}"
            )
            git_lines.append(f"$ git tag -a {tag_name} -m '{tag_message}'")

        if args.dist:
            if not args.build_dir:
                console.print(
                    f"[{STYLE_ERROR}]--build-dir is required when using --dist.[/{STYLE_ERROR}]"
                )
                sys.exit(1)
            try:
                project_name = args.project_name or get_project_name(
                    root_dir, args.build_dir
                )
            except ValueError as exc:
                console.print(f"[{STYLE_ERROR}]{exc}[/{STYLE_ERROR}]")
                sys.exit(1)
            git_lines.append(
                f"$ jrl_release.py --dist  →  {args.build_dir}/{project_name}-{target_version}.tar.gz"
            )
        if args.distcheck and args.build_dir:
            git_lines.append(f"$ cmake --build {args.build_dir} --target distcheck")
        if args.distclean and args.build_dir:
            git_lines.append(f"$ cmake --build {args.build_dir} --target distclean")

        show_dry_run_panel(dry_run_rows, pixi_lock_would_update, git_lines)
        sys.exit(0)
    else:
        if not args.short and args.output_format == "text":
            show_result_panel(pixi_lock_path is not None)

        # Git operations - only perform if explicitly requested
        if args.git_tag is not None and args.git_commit is None:
            console.print(
                f"[{STYLE_WARNING}]Warning: --git-tag used without --git-commit. The tag will point to the current HEAD, not the version bump commit.[/{STYLE_WARNING}]"
            )

        if args.git_commit is not None:
            custom_message = None if args.git_commit is True else args.git_commit
            git_commit_version(
                root_dir,
                target_version,
                args.confirm,
                custom_message,
                updated_file_paths,
            )

        if args.git_tag is not None:
            custom_tag_name = None if args.git_tag is True else args.git_tag
            git_tag_version(
                root_dir,
                target_version,
                args.confirm,
                custom_tag_name,
                args.git_tag_message,
            )

        # --- dist / distcheck / distclean ---
        if args.dist or args.distcheck or args.distclean:
            if not args.build_dir:
                console.print(
                    f"[{STYLE_ERROR}]--build-dir is required when using --dist, --distcheck, or --distclean.[/{STYLE_ERROR}]"
                )
                sys.exit(1)
            try:
                project_name = args.project_name or get_project_name(
                    root_dir, args.build_dir
                )
            except ValueError as exc:
                console.print(f"[{STYLE_ERROR}]{exc}[/{STYLE_ERROR}]")
                sys.exit(1)

            if args.dist:
                tarball = create_dist_tarball(
                    root_dir, project_name, target_version, args.build_dir
                )
                extract_dist_tarball(tarball, args.build_dir)
                run_cmake_configure(root_dir, args.build_dir)

            if args.distcheck:
                try:
                    run_cmake_build_target(args.build_dir, "distcheck")
                except RuntimeError as exc:
                    console.print(
                        f"[{STYLE_ERROR_STRONG}]distcheck failed: {exc}[/{STYLE_ERROR_STRONG}]"
                    )
                    # Roll back the tag so the release can be retried
                    if args.git_tag is not None:
                        custom_tag_name = None if args.git_tag is True else args.git_tag
                        tag_name = (
                            custom_tag_name.format(version=target_version)
                            if custom_tag_name
                            else f"v{target_version}"
                        )
                        console.print(
                            f"[{STYLE_WARNING}]Rolling back tag {tag_name}...[/{STYLE_WARNING}]"
                        )
                        run_git_command(["tag", "-d", tag_name], root_dir)
                    sys.exit(1)

            if args.distclean:
                run_cmake_build_target(args.build_dir, "distclean")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(
            f"\n[{STYLE_WARNING}]Operation cancelled by user (Ctrl+C).[/{STYLE_WARNING}]"
        )
        sys.exit(130)
