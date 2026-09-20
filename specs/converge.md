<!-- ai-generated: 90% - ChatGPT drafted this comparison after reviewing the requirements, API contract and implemented service -->

# Convergence report

The implemented service conforms to the specification created before the source code. R-01 and R-02 are covered by the FastAPI service listening on port 8080 and the `GET /health` response used by Docker Compose health probing. R-03, R-04 and R-20 are covered by the ticket creation endpoint: it validates the required fields, ignores server-owned fields and calculates priority from the published matrix. The selected C3 `matrix` behaviour keeps a VIP ticket at impact 3 and urgency 3 at P4.

R-07, R-08, R-09, R-10 and R-11 are implemented through the five action endpoints and their state checks. The selected C2 `immutable` behaviour rejects reopening a closed ticket, while a resolved ticket may return to `in_progress` within seven days. R-12 through R-17 are covered by the SLA calculation and `/tickets/{id}/sla`: P1 uses the selected C1 `wallclock` behaviour, while P2 to P4 count Europe/Warsaw business hours. The implementation also returns breach and pause values from the current request clock required by R-21.

The local conformance report confirms the compose contract, all 49 HTTP checks, the DECISIONS.md structure and consistency of C1, C2 and C3. The only skipped Core item is the receipt ancestry check, which the course grader evaluates after the final tag is submitted.
