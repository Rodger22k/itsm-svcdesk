---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.99
      threshold_seconds: 0.2
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.2"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
  alerts:
    - {alert: KbSearchAvailabilityBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchAvailabilityBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 90% - ChatGPT Codex drafted the SLO from Mateusz's two measured latency runs -->

# SLO for `GET /kb/search`

## Availability

The availability SLI is the share of valid `/kb/search` requests that do not end in a 5xx response. The objective
is 99% over 30 days. Its 1% error budget is 432 minutes. The dependency produced 6 failures in 2,400 responses in
the first run and 10 in 2,399 responses in the second, so the objective tolerates its small seeded failure rate
without hiding a material outage of the search path.

## Latency

The latency SLI is the share of `/kb/search` requests completed in at most 0.2 seconds. The objective is 99% over
30 days, with the same 1% or 432-minute error budget. The two open-loop runs measured p50 near 24 ms, p95 near
49 ms and p99 at 174.2 ms and 180.2 ms. A 200 ms threshold is therefore above the measured slow mode, is one of
the actual histogram boundaries and remains below the one-second limit used by Lab 6.

## Alerts

| alert | SLI | burn rate | long / short window | budget impact | severity |
|---|---|---:|---|---|---|
| `KbSearchAvailabilityBurnFast` | availability | 14.4 | 1h / 5m | full 30-day budget in 50 hours | P1 page |
| `KbSearchAvailabilityBurnSlow` | availability | 6 | 6h / 30m | full 30-day budget in 5 days | P2 chat |

The fast alert pages because a sustained 14.4-times burn can consume the entire monthly budget in about two days.
The slow alert goes to chat: it is still damaging, but its five-day exhaustion time permits investigation without
waking someone immediately. Both require agreement between a long and a short window, reducing noise and clearing
promptly after the short-window burn ends.

## Buckets

The final ladder has 25 finite boundaries:
`0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.125, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.225, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 2, 5` seconds.
The confirming run placed p99 = 0.1802 seconds in `(0.18, 0.19]`; its width is
`0.01 / 0.1802 = 0.055`, or 5.6%. Ten-millisecond boundaries cover the complete +/-10% neighbourhood of both
measured p99 values. The remaining boundaries retain useful resolution for the fast mode, the SLO threshold and
large regressions without exceeding the 30-boundary budget.
