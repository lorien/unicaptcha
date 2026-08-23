# ADR-0002: CAPTCHA types scope

**Status:** Accepted (amended by ADR-0070: scope extended to eight kinds — FunCaptcha, GeeTest v3/v4 added; reCAPTCHA Enterprise covered as flags on V2/V3)
**Date:** 2026-08-22

## Context

Services support many CAPTCHA families: image, text, reCAPTCHA v2
(checkbox/invisible), reCAPTCHA v3, reCAPTCHA Enterprise, hCaptcha, Cloudflare
Turnstile, GeeTest v3/v4, FunCaptcha/Arkose, KeyCaptcha, audio, Amazon WAF,
DataDome, and more. Each family multiplies challenge classes, solution
classes, and adapter parsing per provider.

## Decision

v1 supports eight CAPTCHA kinds:

1. Image CAPTCHA (picture containing distorted text; input is raw `bytes`)
2. Text CAPTCHA (plain-text question, e.g. "What is two plus three?")
3. reCAPTCHA v2 (checkbox and invisible variants; Enterprise via flags, ADR-0070)
4. reCAPTCHA v3 (Enterprise via flags, ADR-0070)
5. hCaptcha (invisible variant via flag, ADR-0070)
6. FunCaptcha / Arkose (ADR-0070)
7. GeeTest v3 (ADR-0070)
8. GeeTest v4 (ADR-0070)

Turnstile, KeyCaptcha, Capy Puzzle, TikTok, audio, Amazon WAF, DataDome
remain out of scope (deferred by name in deferred.md); the taxonomy
(ADR-0048) keeps adding them additive.

## Rationale

- The original five are the highest-demand kinds across all three
  providers, exercising both solve modes: synchronous answer-in-body
  (image/text) and task-based submit/poll (reCAPTCHA/hCaptcha),
  proving the full engine.
- The ADR-0070 additions (FunCaptcha, GeeTest v3/v4) close the
  top-demand coverage gap competitors exploit, with wide
  multi-provider support and zero structural novelty.
- Eight kinds x three providers is ~24 concrete challenge classes
  and 24 solution classes — bounded, and the adapter SDK keeps the
  remainder third-party-coverable.

## Alternatives considered

- **Everything major** (Enterprise, Turnstile, GeeTest, FunCaptcha, KeyCaptcha,
  audio, WAF): rejected; scope explosion for v1.
- **Minimal set** (image + reCAPTCHA v2 only): rejected; would not exercise
  v3 scoring semantics or invisible variants.
