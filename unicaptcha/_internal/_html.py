"""Stdlib HTML + inline-JS scanning for auto-mode detection (ADR-0077).

Deliberately dependency-free: one ``re`` pass walks the raw HTML left to
right, so widget markup (``<div class="g-recaptcha">`` ...) and inline
``<script>`` widget-construction calls (``grecaptcha.render``,
``initGeetest4``, ...) are emitted in *document order* as
``Signal`` records. ``html.unescape`` recovers literal attribute and
config values.

The module only extracts; ``unicaptcha.detect`` maps signals to
challenge objects. Detection here is intentionally best-effort: a signal
is skipped (never an error) when a widget is referenced but its key is
missing or referenced by a JS variable the library cannot resolve.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Final

__all__ = ["Signal", "scan"]


@dataclass(frozen=True, slots=True)
class Signal:
    """One captcha widget found in the page, in document order.

    ``kind`` is the machine tag, ``fields`` the widget's captured
    config (sitekey / public_key / gt+challenge / captcha_id / ...),
    and ``evidence`` a human-readable snippet of what matched.
    """

    kind: str
    fields: dict[str, str]
    evidence: str


_RECAPTCHA_V2: Final = "recaptcha-v2"
_RECAPTCHA_V3: Final = "recaptcha-v3"
_HCAPTCHA: Final = "hcaptcha"
_TURNSTILE: Final = "turnstile"
_FUNCAPTCHA: Final = "funcaptcha"
_GEETEST_V3: Final = "geetest-v3"
_GEETEST_V4: Final = "geetest-v4"

_DIV_CLASSES: Final = {
    "g-recaptcha": _RECAPTCHA_V2,
    "h-captcha": _HCAPTCHA,
    "cf-turnstile": _TURNSTILE,
}

# One alternation keeps elements and inline JS calls in document order.
_TOKEN: Final = re.compile(
    r"<(?P<tag>div|iframe)\b(?P<attrs>[^>]*)>"
    r"|(?P<js>"
    r"(?:grecaptcha\.render|grecaptcha\.execute|hcaptcha\.render"
    r"|turnstile\.render|initGeetest4|initGeetest)\s*\()",
    re.IGNORECASE,
)

_ATTR: Final = re.compile(
    r"""([\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
    re.IGNORECASE,
)

_JS_KV: Final = re.compile(
    r"""([A-Za-z_]\w*)\s*:\s*(?:"([^"]*)"|'([^']*)'|([A-Za-z0-9_.+-]+))"""
)


def _parse_attrs(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _ATTR.finditer(raw):
        value = match.group(2) or match.group(3) or match.group(4) or ""
        out[match.group(1).lower()] = html.unescape(value)
    return out


def _balanced_end(text: str, start: int) -> int:
    """Index just past the ``)`` closing the ``(`` opened at ``start``."""
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(text)


def _js_params(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _JS_KV.finditer(body):
        out[match.group(1)] = html.unescape(
            match.group(2) or match.group(3) or match.group(4) or ""
        )
    return out


def _element_signal(tag: str, attrs: str) -> Signal | None:
    fields = _parse_attrs(attrs)
    if tag == "div":
        class_names = fields.get("class", "").split()
        for token, kind in _DIV_CLASSES.items():
            if token not in class_names:
                continue
            sitekey = fields.get("data-sitekey") or fields.get("sitekey")
            if not sitekey:
                return None
            if kind == _RECAPTCHA_V2:
                invisible = fields.get("data-size", "") == "invisible"
                return Signal(
                    kind,
                    {"sitekey": sitekey, "invisible": "1" if invisible else "0"},
                    f'<div class="{token}" data-sitekey="{sitekey}">',
                )
            if kind == _HCAPTCHA:
                invisible = fields.get("data-size", "") == "invisible"
                out = {
                    "sitekey": sitekey,
                    "is_invisible": "1" if invisible else "0",
                }
                if fields.get("data-rqdata"):
                    out["rqdata"] = fields["data-rqdata"]
                return Signal(
                    kind, out, f'<div class="{token}" data-sitekey="{sitekey}">'
                )
            # Turnstile.
            out = {"sitekey": sitekey}
            for attr, key in (
                ("data-action", "action"),
                ("data-c-data", "c_data"),
                ("data-chl-page-data", "chl_page_data"),
            ):
                if fields.get(attr):
                    out[key] = fields[attr]
            return Signal(kind, out, f'<div class="{token}" data-sitekey="{sitekey}">')
    if tag == "iframe":
        public_key = fields.get("data-pkey")
        if public_key:
            return Signal(
                _FUNCAPTCHA,
                {"public_key": public_key},
                f'<iframe data-pkey="{public_key}">',
            )
    return None


def _js_signal(call: str, body: str) -> Signal | None:
    lower = call.lower()
    if lower.startswith("grecaptcha.render"):
        params = _js_params(body)
        sitekey = params.get("sitekey")
        if not sitekey:
            return None
        invisible = params.get("size") == "invisible"
        return Signal(
            _RECAPTCHA_V2,
            {"sitekey": sitekey, "invisible": "1" if invisible else "0"},
            f"grecaptcha.render(..., {{sitekey: {sitekey!r}}})",
        )
    if lower.startswith("grecaptcha.execute"):
        match = re.match(r"""\s*(?:"([^"]*)"|'([^']*)')""", body)
        if match is None:
            # Bare ``grecaptcha.execute()`` belongs to a v2-invisible widget
            # already captured via render; no sitekey to build from.
            return None
        sitekey = html.unescape(match.group(1) or match.group(2) or "")
        if not sitekey:
            return None
        params = _js_params(body)
        out = {"sitekey": sitekey}
        if params.get("action"):
            out["action"] = params["action"]
        return Signal(
            _RECAPTCHA_V3,
            out,
            f"grecaptcha.execute({sitekey!r}, {{action: {out.get('action')!r}}})",
        )
    if lower.startswith("hcaptcha.render"):
        params = _js_params(body)
        sitekey = params.get("sitekey")
        if not sitekey:
            return None
        out = {
            "sitekey": sitekey,
            "is_invisible": "1" if params.get("size") == "invisible" else "0",
        }
        if params.get("rqdata"):
            out["rqdata"] = params["rqdata"]
        return Signal(_HCAPTCHA, out, f"hcaptcha.render(..., {{sitekey: {sitekey!r}}})")
    if lower.startswith("turnstile.render"):
        params = _js_params(body)
        sitekey = params.get("sitekey")
        if not sitekey:
            return None
        out = {"sitekey": sitekey}
        for key in ("action", "c_data", "chl_page_data"):
            if params.get(key):
                out[key] = params[key]
        return Signal(
            _TURNSTILE, out, f"turnstile.render(..., {{sitekey: {sitekey!r}}})"
        )
    if lower.startswith("initgeetest4"):
        params = _js_params(body)
        captcha_id = params.get("captcha_id") or params.get("captchaId")
        if not captcha_id:
            return None
        return Signal(
            _GEETEST_V4,
            {"captcha_id": captcha_id},
            f"initGeetest4({{captcha_id: {captcha_id!r}}})",
        )
    if lower.startswith("initgeetest"):
        params = _js_params(body)
        gt = params.get("gt")
        challenge = params.get("challenge")
        if not gt or not challenge:
            return None
        return Signal(
            _GEETEST_V3,
            {"gt_key": gt, "challenge": challenge},
            f"initGeetest({{gt: {gt!r}, challenge: {challenge!r}}})",
        )
    return None


def scan(html_text: str) -> tuple[Signal, ...]:
    """Extract captcha-widget signals from a page, in document order."""
    out: list[Signal] = []
    for match in _TOKEN.finditer(html_text):
        if match.group("js") is not None:
            start = match.start() + match.group("js").rfind("(")
            end = _balanced_end(html_text, start)
            signal = _js_signal(match.group("js"), html_text[start + 1 : end - 1])
        else:
            signal = _element_signal(match.group("tag"), match.group("attrs"))
        if signal is not None:
            out.append(signal)
    return tuple(out)
