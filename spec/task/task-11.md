# Task 11: 2Captcha adapter + facade

Status: done

First read `var/analysis-py-2captcha-python.md` (note: that SDK is the
legacy `in.php` protocol — modern JSON field mapping is in
architecture.md §2).

Implement `provider/twocaptcha/`:

- `challenge.py`: concrete challenge subclasses per ADR-0076 field table
  (all nine kinds; provider extras + wire mapping).
- `solution.py`: concrete solution subclasses.
- `adapter.py`: `TwoCaptchaAdapter` (modern JSON API, `createTask` /
  `getTaskResult`), payload build + parse per ADR-0076/0040, error
  mapping, report pairs, endpoints.
- `client.py`: `TwoCaptchaClient` / `AsyncTwoCaptchaClient` facades
  (constructor parity: `api_key` positional + keyword-only `base_url`,
  `referral`, and every client kwarg; convenience solve methods per kind;
  aux ops; submit/wait/wait_ref).
- Register in package re-exports.

References: ADR-0001, ADR-0007, ADR-0051, ADR-0061, ADR-0076, ADR-0040,
ADR-0041.

Done:

- `challenge.py`: nine concrete frozen-slots challenge subclasses with
  ADR-0076 extras (`phrase/case/numeric/math/min_len/max_len/lang/comment`
  on image; `lang` on text; enterprise/context fields inherited; FunCaptcha
  `data`/`service_url`; GeeTest v3 `api_server`, v4 `risk_type`; proxy/
  worker-context fields per the §2 table). Validation extends the bases.
- `solution.py`: nine concrete solution subclasses.
- `adapter.py`: `TwoCaptchaAdapter` ("twocaptcha",
  https://api.2captcha.com) — full envelope builder (`clientKey`, `task`,
  trinary `softId` referral; project id unregistered → True embeds
  nothing), wire mapping corrected against live API docs
  (`minLength`/`maxLength`, `recaptchaDataSValue` token semantics,
  Enterprise-task types for v2, `isEnterprise` for v3, GeeTest v4 via
  `version`+`initParameters`, reports on `/reportCorrect|reportIncorrect`),
  lenient JSON parsing (ADR-0040) with error-code → ErrorKind table,
  4-state `parse_task_status` (unsolvable / unknown-task codes), instant
  answer fast path (ADR-0075), balance, enabled good/bad report pairs.
- `client.py`: sync + async facades (peers over own TaskEngine), full
  constructor parity minus `adapters`, nine typed `solve_*` methods with
  time/retry/on_event parity and PRE_FLIGHT_FAILED emission on challenge
  validation faults, two-phase submit/wait/wait_ref, aux ops accepting
  `TaskRef | int`.
- Package re-exports in `provider/twocaptcha/__init__.py`.
- Tests: `tests/test_twocaptcha.py` (25 tests) covering challenges,
  payloads per kind, softId, parse states/shapes, error mapping, report
  pairs, sync+async facade round trips over respx, wrong-provider ref
  rejection.
- Owner decisions during session: report pairs stay modern-API-only after
  competitor research (`python-rucaptcha` precedent verified; legacy-only
  SDKs mislead); `referral=True` embeds nothing until an affiliate id is
  registered.
