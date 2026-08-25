# Task 8: HTTP layer

Status: new

Implement the internal HTTP layer behind the public Protocol:

- httpx wiring: `NetworkConfig.timeout` maps to `httpx.Timeout(timeout)`,
  per-stage; `max_connections` / `max_keepalive_connections`.
- Per-request User-Agent (constructor `user_agent=`); default from
  ADR-0026.
- Ownership rules: library-constructed HTTP layer closed by `close()`;
  caller-injected `network_client` never closed; `network=...` plus
  injected client rejected (`InvalidConfigError`, mutual exclusion).
- Sole injection seam for network resources; engine builds URLs as
  `adapter.base_url + adapter.endpoints.<operation>`.

References: ADR-0024, ADR-0026, ADR-0041, ADR-0049, ADR-0073.