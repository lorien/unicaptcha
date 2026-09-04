"""Release-consistency guard tests (scripts/release_check.py).

Covers the green path (which the real CHANGELOG cannot yet exercise, since
no ``## [<version>]`` release section exists) plus both fail modes, run via
subprocess so the real CLI entry point is tested.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from unicaptcha._version import __version__

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "release_check.py"


def _run(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
        check=False,
    )


def _changelog(tmp_path: Path, *, with_section: bool) -> Path:
    path = tmp_path / "CHANGELOG.md"
    body = "# Changelog\n\n## [Unreleased]\n\n- something\n"
    if with_section:
        body += f"\n## [{__version__}] - 2026-09-04\n\n- release\n"
    path.write_text(body, encoding="utf-8")
    return path


def test_release_consistent(tmp_path: Path) -> None:
    changelog = _changelog(tmp_path, with_section=True)
    proc = _run(f"--tag=v{__version__}", f"--changelog={changelog}")
    assert proc.returncode == 0
    assert "release-consistent" in proc.stdout


def test_tag_version_mismatch_fails(tmp_path: Path) -> None:
    changelog = _changelog(tmp_path, with_section=True)
    proc = _run("--tag=v999.0.0", f"--changelog={changelog}")
    assert proc.returncode == 1
    assert "!=" in proc.stdout


def test_missing_changelog_section_fails(tmp_path: Path) -> None:
    changelog = _changelog(tmp_path, with_section=False)
    proc = _run(f"--tag=v{__version__}", f"--changelog={changelog}")
    assert proc.returncode == 1
    assert f"no [{__version__}] section" in proc.stdout


def test_missing_tag_fails() -> None:
    env = os.environ.copy()
    env.pop("GITHUB_REF_NAME", None)
    proc = _run("--changelog=CHANGELOG.md", env=env)
    assert proc.returncode == 1
    assert "no tag" in proc.stdout


@pytest.mark.parametrize("env_value", ["", "v0.0.0"])
def test_ci_reads_github_ref_name(tmp_path: Path, env_value: str) -> None:
    changelog = _changelog(tmp_path, with_section=True)
    env = os.environ.copy()
    env["GITHUB_REF_NAME"] = env_value
    expected = 0 if env_value == f"v{__version__}" else 1
    proc = _run(f"--changelog={changelog}", env=env)
    assert proc.returncode == expected
