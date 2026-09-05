# Detect

HTML captcha detection and the auto-solve result. `detect` parses a
page's source (stdlib only) and returns the captchas it finds as
ready-to-solve kind-base challenges; `auto_solve` on `Solver` /
`AsyncSolver` solves the first match and returns an `AutoSolveResult`
whose `fill` map tells the caller which DOM field each solved value
belongs to.

::: unicaptcha.detect