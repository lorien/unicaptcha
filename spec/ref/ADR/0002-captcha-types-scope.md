# ADR-0002: CAPTCHA types scope

**Status:** Accepted
**Date:** 2026-08-22

## Context

Services support many CAPTCHA families: image, text, reCAPTCHA v2
(checkbox/invisible), reCAPTCHA v3, reCAPTCHA Enterprise, hCaptcha, Cloudflare
Turnstile, GeeTest v3/v4, FunCaptcha/Arkose, KeyCaptcha, audio, Amazon WAF,
DataDome, and more. Each family multiplies challenge classes, solution
classes, and adapter parsing per provider.

## Decision

v1 supports five CAPTCHA kinds:

1. Image CAPTCHA (picture containing distorted text; input is raw `bytes`)
2. Text CAPTCHA (plain-text question, e.g. "What is two plus three?")
3. reCAPTCHA v2 (checkbox and invisible variants)
4. reCAPTCHA v3
5. hCaptcha

reCAPTCHA Enterprise-specific parameters, Turnstile, GeeTest, FunCaptcha and
others are out of scope for v1; the taxonomy (ADR-0048) keeps adding them
additive.

## Rationale

- The chosen five are the highest-demand kinds across all three providers.
- They exercise both solve modes: synchronous answer-in-body (image/text)
  and task-based submit/poll (reCAPTCHA/hCaptcha), proving the full engine.
- Five kinds x three providers is already 15 concrete challenge classes and
  15 solution classes; more would bloat v1 without validating new design
  territory.

## Alternatives considered

- **Everything major** (Enterprise, Turnstile, GeeTest, FunCaptcha, KeyCaptcha,
  audio, WAF): rejected; scope explosion for v1.
- **Minimal set** (image + reCAPTCHA v2 only): rejected; would not exercise
  v3 scoring semantics or invisible variants.
