# ADR-0063: Accept plain `str` api_key in constructors

**Status:** Accepted (amends ADR-0014, ADR-0053, ADR-0061)
**Date:** 2026-08-23

## Context

Constructing a solver requires wrapping every key in `SecretStr(...)`
by hand:

```python
Solver(adapters=[TwoCaptchaAdapter(api_key=SecretStr("..."))])
```

Compact-API review (session 2026-08-23) found the wrap to be the
largest share of setup ceremony. ADR-0014's actual guarantees —
constructor-only delivery, `SecretStr` storage, masking in
repr/str/logs/events — nowhere require the *caller* to do the
wrapping; the annotation was a sketch detail, never an argued
decision. (The incidental "the signature reminds you it's a secret"
effect was weighed as a cost of this ADR and judged insufficient.)

## Decision

- `BaseAdapter.__init__(api_key: SecretStr | str,
  base_url: str | None = None)` accepts either form; a plain `str` is
  **wrapped into `SecretStr` at construction** (normalization at the
  boundary).
- The stored type and any public attribute remain `SecretStr`; all
  ADR-0014 no-leak guarantees are unchanged (repr/str masking, log
  scrubbing, defensive raw_response scrubbing, credential-free
  TaskEvent).
- Facade constructors accept the same union via parity (ADR-0061).
- `api_key` stays the first positional parameter:
  `TwoCaptchaAdapter("...")`.

```python
Solver(adapters=[TwoCaptchaAdapter("..."), CapMonsterAdapter("...")])
```

## Rationale

- The ceremony bought no safety: the library wraps at the boundary,
  so a hand-wrapped key and a plain one are indistinguishable one
  line later. Removing it costs nothing enforceable.
- Explicit `SecretStr` remains available and behaves identically —
  no caller is broken, no style is forbidden.

## Alternatives considered

- **SecretStr-only signatures** (status quo): rejected; ceremony
  without added safety.
- **`from_env()` helpers**: already rejected by owner (ADR-0014);
  unchanged.
- **Magic provider-selection kwargs on the solver** (option D of the
  review, `Solver(twocaptcha=key, ...)`): rejected; stringly
  provider selection breaks the adapter registry's uniformity
  (ADR-0005, ADR-0052).
