---
actual_minutes: 25
ratio: 0.14
---
<!-- ai-generated: 90% - ChatGPT drafted the measurement summary from the recorded timestamps and test results -->

# METR n=1 self-replication

- Predicted minutes: 180
- Actual minutes: 25
- Ratio actual/predicted: 0.14

The measured feature was the DORA metrics calculation module at `src/dora_metrics.py`. Work started only after the prediction had been committed, pushed and receipted against commit `02e98e3`. The implementation was considered complete when the module reproduced every field of the published practice result, the API integration test passed, and the gaming conservation, improvement and harm checks passed.

The actual time was substantially below the prediction because the specification was unusually complete: it provided stable rule identifiers, an exact practice fixture and the expected result for every output field. AI assistance converted those explicit rules into an initial implementation quickly, while deterministic comparisons exposed mistakes without manual arithmetic. The result should not be generalized to a less specified feature. A large part of the usual engineering uncertainty was removed by the published answer key, and the hidden Tier B fixture still remains the important test of whether the implementation follows the rules rather than memorizing the practice values.
