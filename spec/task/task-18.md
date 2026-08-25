# Task 18: README + CHANGELOG

Status: new

- README: finalized usage per the implemented API (universal + facade
  clients, kind list, two-phase batch, custom providers / adapter SDK,
  referral note, base-URL mirrors such as RuCaptcha).
- CHANGELOG: Keep-a-Changelog with an "Unreleased" section summarizing
  the v1 implementation; static version stays 0.1.0.
- Release-consistency CI guards: tag == pyproject version == matching
  CHANGELOG section.

References: ADR-0021, ADR-0022, ADR-0023, ADR-0072.