---
lab4_postmortem:
  ticket: "3ba75e92-1b55-483b-a69e-6097c02b182c"
  detecting_alert: ShopCheckoutSlow
  onset: 2026-10-12T05:01:00Z
  detection: 2026-10-12T05:06:19Z
  acknowledgement: 2026-10-12T05:06:56Z
  recovery: 2026-10-12T05:08:19Z
  mttd_seconds: 319
  mtta_seconds: 37
  mttr_seconds: 439
  identified_flags: [adFailure, intlShippingSlowdown, emailMemoryLeak]
---
<!-- ai-generated: 80% - ChatGPT drafted the document from the student's PromQL results, and the student verified the incident evidence -->

# Postmortem: slow checkout, failed advertisements and rising email memory

## Date

The incident occurred on 12 October 2026, and this postmortem was completed after the recorded telemetry and ticket had been reviewed on 24 October 2026.

## Authors

Mateusz (`Rodger22k`) prepared the report in the on-call engineer role, using the immutable incident snapshot and the service-desk ticket as the sources of record.

## Status

The incident is closed because service recovered at 05:08:19 UTC. The problem record remains open and the preventive action items are still in progress.

## Summary

Three injected faults degraded the shop for 439 seconds: advertisement requests failed, international shipping made checkout requests slow, and the email service consumed increasing memory. `ShopCheckoutSlow` paged the on-call engineer, who acknowledged the ticket 37 seconds after detection.

## Impact

Checkout users experienced long tail latency. At 05:07:00 UTC, `histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="shipping",span_name="POST /ship-order"}[5m])))` returned approximately 8,850 ms. The related checkout `PlaceOrder` path had a p99 of approximately 8,800 ms.

Advertisement retrieval also failed during the fault. `sum by (service_name,span_name) (rate(traces_span_metrics_calls_total{status_code="STATUS_CODE_ERROR"}[5m])) > 0` returned 0.00833 failed `ad/oteldemo.AdService/GetAds` spans per second at 05:07:00 UTC, with matching failures propagated through frontend and frontend-proxy spans.

The resource fault was visible in `max(container_memory_usage_total_bytes{container_name="email"})`: email memory increased from 59,756,544 bytes at 04:58:00 UTC to 74,592,256 bytes at 05:07:00 UTC. Recommendation memory remained nearly unchanged, which separated the email leak from a recommendation-cache failure.

## Root Causes

`adFailure` caused one in ten advertisement lookups to fail and propagated those failures toward the frontend. `intlShippingSlowdown` delayed non-US shipping work and produced the approximately 8.85-second shipping p99 seen in the checkout path. `emailMemoryLeak` continuously increased the email container's memory use and created a risk of an out-of-memory restart.

## Trigger

The recorded injector activated all three selected feature flags at 05:01:00 UTC after the healthy baseline. Ordinary checkout and advertisement traffic then exercised the faulty code paths.

## Resolution

The response removed the checkout-impacting shipping slowdown first, then disabled advertisement failures and the email memory leak. The service recovered at 05:08:19 UTC, after which the detecting alert was no longer firing and the incident snapshot was taken.

## Detection

The `ShopCheckoutSlow` P1 alert detected user-visible checkout latency at 05:06:19 UTC, 319 seconds after onset. The ticket was created at 05:06:36 UTC and acknowledged at 05:06:56 UTC. Without telemetry and the alert, customers or the synthetic load generator would have been the first observers of slow checkout operations.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a shipping server-span p99 alert that distinguishes domestic and international checkout paths. | mitigate | Checkout observability owner | ITSM-401 |
| Add an AdService/GetAds error-ratio alert and dashboard panel separate from flagd stream errors. | mitigate | Frontend platform owner | ITSM-402 |
| Enforce an email-container memory limit and add a leak regression test before deployment. | prevent | Messaging service owner | ITSM-403 |
| Add the verified incident PromQL queries and expected labels to the on-call runbook. | process | Service reliability owner | ITSM-404 |

## Lessons Learned

### What went well

The symptom-based P1 alert detected the customer-facing checkout delay, the service-desk ticket was acknowledged in 37 seconds, and the immutable snapshot preserved enough telemetry to separate three concurrent faults.

### What went wrong

There was no focused shipping-latency alert, so the first page named the checkout symptom instead of its dependency. Both AI investigators also confused counter growth with duration evidence, which required every hypothesis to be checked independently.

### Where we got lucky

The incident lasted only 439 seconds, the email leak had not yet caused a container restart, and the shipping slowdown affected a subset of orders instead of stopping all checkout traffic.

## Timeline

- 05:00:30 UTC - the last checked baseline was quiet; shipping latency and email memory were still near their normal levels.
- 05:01:00 UTC - `adFailure`, `intlShippingSlowdown` and `emailMemoryLeak` activated and the incident began.
- 05:06:19 UTC - `ShopCheckoutSlow` fired; MTTD was 319 seconds.
- 05:06:36 UTC - service-desk incident `3ba75e92-1b55-483b-a69e-6097c02b182c` was created as P1.
- 05:06:56 UTC - the on-call engineer acknowledged the ticket; MTTA was 37 seconds.
- 05:07:00 UTC - snapshot queries showed shipping p99 near 8,850 ms, AdService/GetAds errors at 0.00833/s and rising email memory.
- 05:08:19 UTC - all three faults were disabled and the service recovered; MTTR was 439 seconds.

## Supporting information

The evidence is retained in `incident/tsdb-snapshot.tar.gz` and `incident/ticket.json`. The incident clocks were independently recomputed by `itsmlab incident 4`. The PromQL results, `ai-rca-eval.json`, `ai-rca-eval-2.json` and `ai-rca/COMPARISON.md` document why the agents' proposed load and checkout causes were not accepted without measurement.

## Problem record

Incident record: 3ba75e92-1b55-483b-a69e-6097c02b182c, closed after service recovery.

Root cause: Concurrent advertisement failure, international shipping delay and email-service memory leakage activated by the incident injector.

Known error: The current shop configuration permits these feature-controlled dependency failures without targeted shipping and memory-leak detection.

Workaround: Disable the three affected feature flags, prioritising the shipping slowdown to restore checkout before clearing secondary advertisement and memory symptoms.
