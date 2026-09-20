---
svcdesk_decisions:
  C1: wallclock
  C2: immutable
  C3: matrix
---
<!-- ai-generated: 90% - ChatGPT drafted this document; I checked the selected resolutions against the API contract -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1 acknowledgement and resolution deadlines use wall-clock time, including evenings, nights and weekends.

**Rejected alternative:** We rejected the business-hours clock for P1 because a critical incident must not wait until Monday morning.

**Reason:** P1 means that work is stopped for the whole organisation, so the fastest response is more important than office hours.

**Service owner:** The Head of IT Operations owns this decision because that role is accountable for critical incident response.

**Customer outcome:** Reporters receive urgent handling of organisation-wide failures even when an incident begins outside business hours.

## C2 - Closed tickets and reopening

**Decision:** A closed ticket is immutable and reopening it always returns HTTP 409 Conflict.

**Rejected alternative:** We rejected reopening closed tickets because closure represents a confirmed and final service-desk record.

**Reason:** A new ticket with `related_to` preserves the history and avoids changing the audit trail of a completed case.

**Service owner:** The Service Desk Manager owns this decision because that role is responsible for reliable records and reporting.

**Customer outcome:** Reporters can still report a recurring issue, while the desk keeps a clear history of the original resolution.

## C3 - VIP reporters and the priority matrix

**Decision:** Priority is determined only by the impact and urgency matrix; the VIP flag does not modify it.

**Rejected alternative:** We rejected raising VIP P3 and P4 tickets to P2 because priority must reflect the operational impact.

**Reason:** A transparent matrix prevents personal status from overtaking incidents that affect more employees or services.

**Service owner:** The Service Desk Product Owner owns this decision because that role defines fair prioritisation for the organisation.

**Customer outcome:** Every reporter receives predictable treatment, while genuinely high-impact incidents remain at the front of the queue.