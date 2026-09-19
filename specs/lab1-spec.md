<!-- ai-generated: 90% - ChatGPT drafted this specification; I reviewed the requirements and selected the three resolutions -->



\# svcdesk - Lab 1 specification



\## 1. Objective



svcdesk is a JSON HTTP service for managing internal IT tickets. It exposes its API on port 8080 and provides a health endpoint for monitoring. The service creates, stores, lists, retrieves and changes the state of tickets while calculating priority and SLA deadlines.



\## 2. Ticket creation and validation



A client creates a ticket with `POST /tickets`. A valid ticket requires a title from 1 to 200 characters, a reporter name from 1 to 100 characters, and integer values of impact and urgency from 1 to 3. Description is optional and may contain at most 4000 characters. Reporter e-mail, VIP flag and `related\_to` are optional.



The service assigns an opaque unique identifier and owns the priority, state, timestamps and SLA fields. Client-supplied server-owned or unknown fields are ignored. Invalid requests return HTTP 400 or 422 with a JSON body containing a top-level `error` object. Unknown ticket identifiers and unknown paths return JSON 404 responses.



\## 3. Ticket API and lifecycle



`GET /health` returns HTTP 200 with `status` equal to `ok` and `service` equal to `svcdesk`. `GET /tickets` returns all tickets matching optional exact `state` and `priority` filters. `GET /tickets/{id}` returns one ticket, while `GET /tickets/{id}/sla` returns its SLA status.



A ticket begins in `new`. The only valid state transitions are:



1\. `new` to `acknowledged` through `POST /tickets/{id}/ack`;

2\. `acknowledged` to `in\_progress` through `POST /tickets/{id}/start`;

3\. `in\_progress` to `resolved` through `POST /tickets/{id}/resolve`;

4\. `resolved` to `closed` through `POST /tickets/{id}/close`.



Invalid transitions return HTTP 409. A valid transition returns the complete ticket and records its action timestamp using the request clock.



\## 4. Priority and decision C3



Priority follows the impact and urgency matrix defined in API.md. This specification chooses `C3: matrix`: the VIP flag is stored but does not alter the calculated priority. A VIP ticket with impact 3 and urgency 3 therefore has priority `P4`. A client-provided `priority` field is ignored.



\## 5. Reopening and decision C2



A resolved ticket may be reopened within seven days of `resolved\_at`; it returns to `in\_progress` and clears `resolved\_at` and `closed\_at`. This specification chooses `C2: immutable`: a closed ticket is never reopened and always returns HTTP 409. A new related ticket must be created instead.



\## 6. SLA and decision C1



Each ticket receives acknowledgement and resolution targets from its computed priority. The service uses RFC 3339 instants and returns UTC timestamps with a `Z` suffix.



This specification chooses `C1: wallclock`. P1 acknowledgement and resolution deadlines use wall-clock time, including evenings and weekends. P2, P3 and P4 deadlines use the Europe/Warsaw business-hours clock: Monday to Friday, from 08:00 inclusive to 16:00 exclusive. The implementation must reproduce all SLA vectors from API.md, including the closing-time tie rule and daylight-saving offsets.



`GET /tickets/{id}/sla` returns priority, both due instants, acknowledgement breach, resolution breach and pause status. A deadline is breached only when the event happened after its due instant or is still missing after the due instant. Equality is not a breach.



\## 7. Test clock, deployment and persistence



When `SVCDESK\_TEST\_CLOCK` is enabled, an RFC 3339 `X-Test-Clock` request header is used as the current instant for that request only. A malformed header returns HTTP 400 or 422. Without a valid test clock, the service uses real UTC time.



The project defines a Docker Compose service named `svcdesk`, built from this repository and listening on container port 8080. It uses no host-path bind mounts and needs no network access after its image has been built. Tickets persist across a container restart.



\## 8. Acceptance criteria



The implementation must satisfy the published Core checks: Docker Compose startup and health endpoint, all HTTP conformance checks, the required DECISIONS.md structure, consistency between declared and observed C1/C2/C3 values, and the specification-before-code receipt rule.

