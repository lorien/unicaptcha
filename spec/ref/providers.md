# Supported providers

The v1 provider set (ADR-0001, amended by ADR-0071): four services speaking
the JSON-family `createTask` / `getTaskResult` protocol.

## 2Captcha

Kind: twocaptcha
Website: https://2captcha.com
Repo: https://github.com/2captcha/2captcha-python

## Anti-Captcha

Kind: anti-captcha
Website: https://anti-captcha.com
Repo: https://github.com/anti-captcha/anticaptcha-python

## CapMonster Cloud

Kind: capmonster
Website: https://capmonster.cloud
Repo: https://github.com/CapMonsterCloud/capmonster-python-captcha-solver

## Capsolver

Kind: capsolver
Website: https://www.capsolver.com
Repo: https://github.com/capsolver/capsolver-python

## Mirrors

RuCaptcha and other 2Captcha-protocol mirrors are not shipped providers.
They work by overriding the 2Captcha adapter's base_url (ADR-0071).