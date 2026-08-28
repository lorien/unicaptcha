"""Examples consistency guards.

Every file under ``examples/`` must stay syntactically valid
(``compile()``), and every ``examples/`` path referenced from the READMEs
must resolve to a real file. Scripts are not executed (they solve real
captchas); import-level correctness is covered by the library's own tests
and the API-parity facades they call.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


def _example_sources() -> list[tuple[Path, str]]:
    return [
        (path, path.read_text(encoding="utf-8"))
        for path in sorted(EXAMPLES.rglob("*.py"))
    ]


def test_examples_compile() -> None:
    sources = _example_sources()
    assert sources, "examples/ contains no Python files"
    for path, source in sources:
        compile(source, str(path), "exec")


def test_examples_are_provider_annotated() -> None:
    for path, source in _example_sources():
        assert "Anti-Captcha" in source and "Capsolver" in source, (
            f"{path.name} must name the other providers in its header note"
        )


def test_readme_links_resolve() -> None:
    for readme in (EXAMPLES / "README.md", ROOT / "README.md"):
        for match in re.finditer(r"\((examples/[^)#\s]+)\)", readme.read_text()):
            assert (ROOT / match.group(1)).exists(), (
                f"{readme.name} links to missing {match.group(1)}"
            )


def test_sync_async_mirrors_match() -> None:
    sync = sorted(p.name for p in (EXAMPLES / "sync").glob("*.py"))
    async_names = sorted(p.name for p in (EXAMPLES / "async").glob("*.py"))
    assert sync == async_names, "sync/ and async/ examples must mirror 1:1"
    expected = {
        "aux_ops.py",
        "errors.py",
        "events.py",
        "funcaptcha.py",
        "geetest_v3.py",
        "geetest_v4.py",
        "hcaptcha.py",
        "image.py",
        "proxy.py",
        "recaptcha_v2.py",
        "recaptcha_v3.py",
        "text.py",
        "turnstile.py",
        "two_phase.py",
        "universal_client.py",
    }
    assert set(sync) == expected
