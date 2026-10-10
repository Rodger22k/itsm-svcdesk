<!-- ai-generated: 90% - ChatGPT Codex drafted the explanation from Mateusz's Toxiproxy measurement -->

# Client-server latency gap

The experiment places Toxiproxy in front of `svcdesk` and adds a downstream latency toxic with 100 ms latency
and 10 ms jitter. The client therefore observes the service processing time together with the delay introduced
after the response leaves the service. The server-side Prometheus histogram records only the time spent handling
the request inside `svcdesk`, including its call to `kb-index`; it cannot see the downstream network delay added
later by the proxy. Consequently, the client p99 should be higher than the p99 calculated from the service
histogram. The value in `gap.json` is the client p99 minus the server p99 from the same open-loop run. Jitter and
percentile interpolation mean this difference need not equal exactly 100 ms, but it should remain close enough to
the configured toxic and be reproducible within the checker's stated tolerance.
