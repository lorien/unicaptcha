# Task 11: 2Captcha adapter + facade

Status: new

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