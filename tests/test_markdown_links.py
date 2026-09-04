"""Markdown link checker (README + docs/ + spec/docs/).

Every local relative link in the documentation trees must resolve to a
real file. External URLs (http/https/mailto) and bare anchors are
skipped, so the check is deterministic and offline. Runs in the pytest
suite on every push/PR.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_TREES = [
    ROOT / "README.md",
    *sorted((ROOT / "docs").rglob("*.md")),
    *sorted((ROOT / "spec/docs").rglob("*.md")),
]

_MD_LINK = re.compile(r"\]\(([^)]+)\)|<(\.{1,2}/[^)>]+)>")


def _local_targets(text: str) -> list[str]:
    """Local relative link targets, skipping external and anchor-only."""
    targets: list[str] = []
    for match in _MD_LINK.finditer(text):
        target = (match.group(1) or match.group(2)).split("#", 1)[0].strip()
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.endswith(".py"):
            continue
        targets.append(target)
    return targets


def _resolve(file: Path, target: str) -> Path | None:
    candidate = (file.parent / target).resolve()
    if candidate.exists():
        return candidate
    root_candidate = (ROOT / target).resolve()
    if root_candidate.exists():
        return root_candidate
    return None


class TestMarkdownLinks(unittest.TestCase):
    def test_local_links_resolve(self) -> None:
        checked = 0
        broken: list[tuple[str, str]] = []
        for file in DOC_TREES:
            for target in _local_targets(file.read_text(encoding="utf-8")):
                checked += 1
                if _resolve(file, target) is None:
                    broken.append((str(file.relative_to(ROOT)), target))
        self.assertTrue(checked, "no local markdown links found to check")
        self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
