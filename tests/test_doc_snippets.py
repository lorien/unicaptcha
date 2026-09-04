"""Doc snippet verification (README + docs/).

Every ```python fence in the end-user documentation must be valid Python,
and its ``unicaptcha`` imports must resolve against the shipped package.
This catches snippet rot that prose review cannot: syntax errors, and
renamed / moved public API names (e.g. a snippet still using an old name
like ``JsonAdapterBase``).
"""

import ast
import importlib
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_FILES = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]

_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _python_blocks() -> list[tuple[str, str]]:
    """``(filename:lineno, source)`` for every ```python fence."""
    blocks: list[tuple[str, str]] = []
    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        for match in _FENCE.finditer(text):
            lineno = text[: match.start()].count("\n") + 1
            blocks.append((f"{path.relative_to(ROOT)}:{lineno}", match.group(1)))
    return blocks


def _wrap_async(src: str) -> str:
    """Wrap a fragment in an async function so top-level ``async with`` /
    ``await`` snippets parse (legitimate in the docs, invalid at module
    scope). Real syntax errors fail again with the original message."""
    return "async def _snippet():\n" + textwrap.indent(src, "    ")


def _parse(src: str, fname: str) -> ast.Module:
    try:
        return ast.parse(src)
    except SyntaxError:
        return ast.parse(_wrap_async(src), filename=fname)


def test_snippets_compile() -> None:
    blocks = _python_blocks()
    assert blocks, "no ```python fences found in README/docs"
    for fname, src in blocks:
        try:
            compile(src, fname, "exec")
        except SyntaxError:
            compile(_wrap_async(src), fname, "exec")


def test_snippet_imports_resolve() -> None:
    for fname, src in _python_blocks():
        tree = _parse(src, fname)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    importlib.import_module(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                module = importlib.import_module(node.module)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    assert hasattr(module, alias.name), (
                        f"{fname}: {node.module} has no attribute {alias.name!r}"
                    )
