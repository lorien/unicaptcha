# Statistics

Cumulative client usage fed by the task-event stream. `StatsCollector`
is a synchronous `on_event` handler that tallies solved/failed tasks and
elapsed time per provider; `snapshot()` returns an immutable `UsageStats`.

::: unicaptcha.stats