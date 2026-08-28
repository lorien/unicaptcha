# Provider fidelity verification

A repeatable procedure for verifying that our adapters speak each
provider's wire contract correctly, and the record of the most recent
verification pass (2026-08-28). Inputs are the vendor clones and
knowledge bases under the gitignored `var/vendor/` tree
(see [vendor.md](vendor.md)).

## Evidence sources

| Provider | Clone (`var/vendor/repo/`) | HEAD | Wire evidence rule |
|---|---|---|---|
| 2Captcha | `2captcha-python` | `b49b908` | SDK speaks the **legacy form API** (`in.php`/`res.php`); it cannot testify for the JSON API. Rule: live-docs verification (task 11, recorded in ADR-0076 §2Captcha table) + legacy-SDK option names where they pass through (`data`/`pagedata`/`action` corroborated). |
| Anti-Captcha | `anticaptcha-python` | `ffda933` | SDK per-kind modules (`anticaptchaofficial/*.py`) build the JSON `task` dict directly — **primary source**. Text has no SDK module (docs-attested only, noted in ADR-0076). |
| CapMonster | `capmonster-python-captcha-solver` | `155ada4` | Pydantic `getTaskDict()` per request model + `examples/` — **primary source** (`requests/*.py`). |
| Capsolver | `capsolver-python` | `8f2ffda` | SDK is dict-driven (no typed models); rule: live docs (`docs.capsolver.com` per-kind pages) + `check.py` task-type list. |

## Algorithm

For each provider × supported kind:

1. **Derive** the expected `createTask` task dict (task-type string +
   field wire names + shape) from the evidence source above, citing the
   vendor file (and example) that attests each field.
2. **Diff** the derived dict against the adapter's `build_payload` output
   for a canonical challenge instance.
3. **Diff** against the golden fixture in `tests/test_golden_payloads.py`.
4. **Classify** the row: `verified` (matches), `fixed` (discrepancy found
   and corrected), or `live-only` (no static evidence; needs a real key).
5. Fix discrepancies in the adapter, then regenerate the golden fixture
   from the vendor-derived expectation (fixtures are never hand-written
   twice).

Auxiliary operations and error tables are verified the same way against
the SDK network layers (`antinetworking.py`, `CapMonsterCloudClient.py`,
`api_requestor.py`) and error modules.

## Verification matrix (2026-08-28 pass)

All 35 kind × provider rows verified; 1 discrepancy found and fixed.
Aux ops (createTask/getTaskResult/getBalance/reportCorrect/reportIncorrect
endpoints, `clientKey` envelope, error-code tables) verified against the
vendor network layers for all four providers.

| Provider | Kind | Status | Evidence |
|---|---|---|---|
| twocaptcha | image, text, reCAPTCHA v2/v3, hCaptcha, FunCaptcha, GeeTest v3/v4, Turnstile | verified | Live-docs verification (task 11, ADR-0076); legacy SDK corroborates Turnstile `data`/`pagedata`/`action` option names (`examples/sync/turnstile_options.py`) |
| anti-captcha | image | verified | `anticaptchaofficial/imagecaptcha.py` (phrase/case/numeric/math/minLength/maxLength/comment/languagePool in task) |
| anti-captcha | text | verified (docs-attested) | No SDK module; ADR-0076 pins `TextCaptchaTask` from live docs — SDK-silent surface |
| anti-captcha | reCAPTCHA v2 | verified | `recaptchav2proxyless.py` (`websiteURL`, `websiteKey`, `websiteSToken`, `recaptchaDataSValue`, `isInvisible`) |
| anti-captcha | reCAPTCHA v3 | verified | `recaptchav3proxyless.py` (`minScore`, `pageAction`) |
| anti-captcha | reCAPTCHA v2 Enterprise | verified | `recaptchav2enterpriseproxyless.py` (`enterprisePayload`) |
| anti-captcha | hCaptcha | verified | `hcaptchaproxyless.py` (`isInvisible`, `enterprisePayload`, `userAgent` — SDK sends always, we send conditionally; absent optionals are compatible) |
| anti-captcha | FunCaptcha | verified | `funcaptchaproxyless.py` (`websitePublicKey`, `data`, `funcaptchaApiJSSubdomain`) |
| anti-captcha | GeeTest v3 | verified | `geetestproxyless.py` (`gt`, `challenge`, `geetestApiServerSubdomain`, `geetestGetLib`) |
| anti-captcha | GeeTest v4 | verified | `geetest_proxyless_example.py` V4 block: `gt` = captcha id, `version=4`, `initParameters` (riskType); adapter matches |
| anti-captcha | Turnstile | verified | `turnstileproxyless.py` (`action`, `cData`, `chlPageData`) |
| capmonster | image | verified | `ImageToTextRequest.getTaskDict` (`body`, `recognizingThreshold`, `CapMonsterModule`, `Case`, `numeric`, `math`) |
| capmonster | reCAPTCHA v2 | verified | `RecaptchaV2Request.getTaskDict` (`recaptchaDataSValue`, `userAgent`, `cookies`, `isInvisible`) |
| capmonster | reCAPTCHA v2 Enterprise | verified | `RecaptchaV2EnterpiseRequest.getTaskDict` (`enterprisePayload` = `{"s": ...}`, `apiDomain`) |
| capmonster | reCAPTCHA v3 | verified | `RecaptchaV3ProxylessRequest` — type `RecaptchaV3TaskProxyless` |
| capmonster | hCaptcha | verified | `HcaptchaRequest.getTaskDict` (`isInvisible`, `data`, `userAgent`, `cookies`, `fallbackToActualUA`) |
| capmonster | FunCaptcha | verified | `FuncaptchaRequest.getTaskDict` (`websitePublicKey`, `funcaptchaApiJSSubdomain`, `data`, `cookies`) |
| capmonster | GeeTest v3 | verified | `GeetestRequest.getTaskDict` — `version` always present; `challenge` required for v3 |
| capmonster | GeeTest v4 | **fixed** | `GeetestRequest` requires `gt` unconditionally; `examples/geeTestv4.py` passes `gt=<id>`, `version=4`, `initParameters={'riskType': ...}`. Adapter was emitting no `gt` and put `captcha_id` inside `initParameters` — corrected: `gt` = captcha id, `initParameters` carries `riskType` only |
| capmonster | Turnstile | verified | `TurnstileRequest.getTaskDict` (`pageAction`, `data`, `pageData`, `cloudflareTaskType`, `htmlPageBase64`, `apiJsUrl`) |
| capsolver | image | verified | `check.py` type list; docs ImageToText (`body`, `module`) |
| capsolver | reCAPTCHA v2 (+Enterprise) | verified | `check.py` types; docs `ReCaptchaV2TaskProxyLess` field names |
| capsolver | reCAPTCHA v3 | verified | `check.py` type; docs (`pageAction`, `minScore`) |
| capsolver | hCaptcha | verified | `check.py` types; docs (`rqdata` top-level, `isEnterprise`) |
| capsolver | FunCaptcha | verified | `check.py` types; docs (`websitePublicKey`) |
| capsolver | GeeTest v3 | verified | docs Geetest page (fetched 2026-08-28): `gt`, `challenge`, `geetestApiServerSubdomain` |
| capsolver | GeeTest v4 | verified | docs Geetest page: `captchaId`, `riskType`, `geetestApiServerSubdomain` |
| capsolver | Turnstile | verified | `AntiTurnstileTaskProxyLess` + `metadata {action, cdata}` (ADR-0076) |

## Live-only items (no static evidence possible)

- 2Captcha JSON-API rows rest solely on the task-11 live verification;
  re-verify on any ADR-0076 amendment.
- Anti-Captcha `TextCaptchaTask`: docs-attested, SDK-silent — a live
  submit is the only stronger evidence.
- Capsolver extra-field tolerance (e.g. our conditional `userAgent` on
  kinds where docs are silent) — verified only by a live submit.

## Re-running the pass

1. `git -C var/vendor/repo/<clone> fetch --depth 1 && git log -1` — note
   new HEADs; re-read changed files.
2. Re-derive expectations per the algorithm; diff against
   `tests/test_golden_payloads.py` (the fixtures must change only when
   the vendor sources changed).
3. Update this matrix with a dated pass note.
