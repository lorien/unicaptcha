"""Release-consistency guard (ADR-0021/0022).

On a ``v*`` tag, CI asserts tag == ``unicaptcha/_version.py`` version == a
matching ``## [<version>]`` CHANGELOG section; drift becomes
unpublishable. Run locally before tagging:

    python scripts/release_check.py --tag v0.1.0

``GITHUB_REF_NAME`` is used when ``--tag`` is omitted (CI).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from unicaptcha._version import __version__  # noqa: E402


def _tag_ok(tag: str | None) -> bool:
    if not tag:
        print("no tag: pass --tag or set GITHUB_REF_NAME")
        return False
    if tag != f"v{__version__}":
        print(f"tag {tag!r} != v{__version__!r}")
        return False
    return True


def _changelog_ok(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if re.search(rf"^## \[{re.escape(__version__)}\]", text, re.M):
        return True
    print(f"{path.name} has no [{__version__}] section")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default=os.environ.get("GITHUB_REF_NAME"))
    parser.add_argument(
        "--changelog",
        type=Path,
        default=ROOT / "CHANGELOG.md",
        help="changelog path (default: CHANGELOG.md)",
    )
    args = parser.parse_args()
    if not (_tag_ok(args.tag) and _changelog_ok(args.changelog)):
        return 1
    print("release-consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
