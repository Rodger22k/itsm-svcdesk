---
lab3_first_draft:
  source: ai
  tool: "ChatGPT Codex (GPT-5), 10 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0, 2.0, 5.0]
  verdict: TODO
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
---
<!-- ai-generated: 95% - ChatGPT Codex proposed the initial ladder and alert; evidence and verdict will be completed after measurement -->

# The assistant's first draft, and two verdicts

## Prompt

Before measuring the service, propose an initial list of Prometheus histogram bucket boundaries in seconds for
`GET /kb/search` and one multiwindow SLO burn-rate alert rule. The endpoint calls an upstream knowledge-base
index. I do not yet know its latency distribution, so state the assumptions and make the proposal something I can
test and revise after an open-loop p99 measurement.

## Answer

Without measurements, I would start with a broad ladder that gives extra resolution between 100 ms and 500 ms,
because an upstream search dependency may have a fast mode in the tens of milliseconds and a slower tail in that
range. I would use these finite boundaries, in seconds:

`[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0, 2.0, 5.0]`

This is only an initial ladder. After an open-loop load test, I would add narrower boundaries around the measured
p99 and keep the total comfortably below 30. For an initial fast availability alert, assuming a 99% availability
objective, I would use a 14.4 burn rate with a 1-hour long window and a 5-minute short window:

```yaml
- alert: KbSearchAvailabilityBurnFast
  expr: |
    (
      sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"5.."}[1h]))
      /
      sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[1h]))
    ) > 14.4 * (1 - 0.99)
    and
    (
      sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"5.."}[5m]))
      /
      sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))
    ) > 14.4 * (1 - 0.99)
  for: 5m
  labels:
    service: svcdesk
    slo: availability
    severity: P1
```

I would validate both the bucket ladder and the alert against measured data before treating either as final. In
particular, the p99 bucket should be narrow enough for the required resolution, and the alert needs unit tests for
its firing edge, quiet condition, and reset after the short window clears.

## Verdict on the draft ladder

TODO after running the published `load 3` measurement. Record the measured p99, its bucket, the relative width,
what `histogram_quantile` could report from that bucket, and whether the ladder resolves the measured p99.

## The draft alert rule

TODO after selecting the final SLO. Explain what was retained from the proposed multiwindow availability alert and
what was changed to match the measured service and the published alert probes.

## Verdict on the instructor's flawed ladder

TODO after running the same measurement. Record the measured p99, its bucket in the instructor's ladder, the
relative width, the possible interpolation range, and why the ladder is refuted.
