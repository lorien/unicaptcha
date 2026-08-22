# ADR-0020: MIT license

**Status:** Accepted
**Date:** 2026-08-22

## Context

unicaptcha is an open-source Python library distributed via PyPI. A license
must be chosen before the first public release. Key considerations:

* As a utility **library** (not an application), maximal downstream
  adoption matters; strong copyleft would deter most potential users.
* CAPTCHA-solving tools operate in a legally gray area (provider ToS,
  potential misuse), so explicit warranty disclaimers and liability
  limitations are important for contributors and maintainers.
* No patent-heavy technology is involved; corporate contributors are
  possible but not the primary audience.

## Decision

Distribute unicaptcha under the **MIT License**.

## Rationale

* Simplest and most permissive widely understood license; zero friction
  for adoption and embedding in any project, including commercial.
* Contains the required "no warranty / limited liability" clauses,
  adequate given the project's gray-area domain.
* Minimal maintenance burden: no NOTICE files, no compatibility
  questions, universally recognized by package ecosystems.

## Alternatives considered

* **Apache-2.0** — permissive with an explicit patent grant and more
  thorough legal language. Rejected as unnecessary rigor: no patent
  exposure, and its NOTICE/attribution machinery adds friction without
  benefit here.
* **BSD-3-Clause** — functionally similar to MIT plus a
  non-endorsement clause. Rejected: adds a clause nobody required.
* **LGPL/MPL-2.0 (weak copyleft)** — rejected: copyleft obligations on
  the library itself reduce adoption for no compensating benefit.
* **GPL-3.0 (strong copyleft)** — rejected: effectively bars commercial
  and proprietary use, unacceptable for a library aiming at wide use.
* **Proprietary / unlicensed** — rejected: project is intended to be
  publicly available on GitHub and PyPI.
