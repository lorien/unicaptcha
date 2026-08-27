"""README consistency guards (ADR-0023: README-only docs for v1).

Prose-only checks that the README stays in sync with the shipped API:
the nine-kind v1 taxonomy and the real (singular ``provider``) import
path. No doctest machinery — plain content assertions.
"""

from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"

KINDS = [
    "Image CAPTCHA",
    "Text CAPTCHA",
    "reCAPTCHA v2",
    "reCAPTCHA v3",
    "hCaptcha",
    "FunCaptcha",
    "GeeTest v3",
    "GeeTest v4",
    "Cloudflare Turnstile",
]


def _section(header: str) -> str:
    text = README.read_text()
    start = text.index(header)
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def test_readme_lists_all_nine_kinds() -> None:
    section = _section("## Supported CAPTCHA kinds (v1)")
    for kind in KINDS:
        assert kind in section, f"README kind list is missing {kind!r}"


def test_readme_uses_singular_provider_import() -> None:
    text = README.read_text()
    assert "unicaptcha.provider.twocaptcha" in text
    assert "unicaptcha.providers." not in text
