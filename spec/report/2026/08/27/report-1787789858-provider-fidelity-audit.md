## Report on task: provider-fidelity audit (2Captcha adapter vs live docs)

### Spec/ADR amendments

- [acted] 2Captcha Turnstile wire names: live docs use lowercase
  `data` (cData value) and `pagedata` (chlPageData value); ADR-0076's
  architecture §2 row said `cData`/`chlPageData`. Row corrected, adapter
  fixed.
- [acted] reCAPTCHA v3 is proxyless-only on all four providers. Live
  2Captcha docs document only `RecaptchaV3TaskProxyless` — ADR-0076's
  "2Captcha additionally exposes a proxy variant (`RecaptchaV3Task`)"
  claim was unverified and wrong; removed from ADR-0076 and the
  architecture coverage boundary. `TwoCaptchaRecaptchaV3Challenge`
  dropped its `proxy`, `user_agent`, and `cookies` fields (owner
  decision), and the v3 docs list no userAgent/cookies fields either.
- [acted] Added deferred item 22 (owner request): a repeatable
  verification method comparing adapter implementations against official
  docs + SDK clones must be developed.

### Future-task notes

- Task 12 (Anti-Captcha): spec text row says `lang→lang` but
  TextCaptchaTask is absent from the official SDK and the apidoc page is
  JS-rendered — verify at implementation; consider aligning with the
  image row's `language_pool→languagePool`. Anti-Captcha Turnstile
  proxy-on sends `isInvisible` (SDK quirk) though no universal field
  exists for it.
- Task 13 (CapMonster): image `numeric` accepts 0/1 only per SDK
  validator (not 2Captcha's 0-4); GeeTest v4 still requires a `gt` value
  in the SDK — verify what it carries at implementation.
- Task 14 (Capsolver): dict-driven SDK exposes enterprise variants
  (`ReCaptchaV2EnterpriseTask[ProxyLess]`,
  `HCaptchaEnterpriseTask[ProxyLess]`) absent from the pinned surface;
  universal challenges carry `is_enterprise` — decide mapping then.

### Tooling/process

- Open items intentionally left `[open]`: 2Captcha v3 `minScore` is
  documented required (0.3/0.7/0.9) while our surface keeps it optional
  without validation; solution-shape dispatch misclassifies v3 answers
  as RecaptchaV2Solution and Turnstile as HCaptchaSolution (shape-keyed
  parsing has no kind context). Both need owner decisions before acting.
- Audit lesson recorded in deferred item 22: manual doc comparison found
  five task-type/wire-name bugs that golden tests could not — because the
  tests asserted the same wrong strings. Fixtures must be derived from
  vendor sources, not hand-written twice.

### Fixed this session

1. `RecaptchaV3Task` → always `RecaptchaV3TaskProxyless` (proxyless-only).
2. Turnstile type made proxyless/proxy-conditional.
3. Turnstile `cData`/`chlPageData` → `data`/`pagedata`.
4. FunCaptcha type made proxyless/proxy-conditional.
5. GeeTest v3 + v4 types made proxyless/proxy-conditional.
6. v3 challenge/facade: `proxy`, `user_agent`, `cookies` removed.
7. Tests updated (26 passing); all static checks clean.
