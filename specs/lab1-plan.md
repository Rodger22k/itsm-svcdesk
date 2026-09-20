<!-- ai-generated: 90% - ChatGPT drafted this implementation plan and task list from the course API contract -->



\# Lab 1 implementation plan and tasks



\## Scope



The service will be implemented in Python 3.13 with FastAPI. It will expose the required JSON API on port 8080 and use SQLite in a Docker named volume so tickets survive a container restart. Docker Compose will build the service from the repository and will not use bind mounts or runtime network access.



\## Fixed decisions



\- C1 is `wallclock`: P1 acknowledgement and resolution targets use wall-clock time. P2, P3 and P4 use Europe/Warsaw business hours.

\- C2 is `immutable`: a resolved ticket may be reopened within seven days, but a closed ticket always returns HTTP 409.

\- C3 is `matrix`: priority comes only from the impact and urgency matrix; VIP status is stored but does not raise priority.



\## Implementation structure



\- `src/main.py` will contain the FastAPI application, routes, validation and error responses.

\- `src/sla.py` will calculate priorities, SLA due instants, business-hours time, breach flags and pause status.

\- `src/storage.py` will persist tickets in SQLite.

\- `requirements.txt`, `Dockerfile` and `docker-compose.yml` will install dependencies during the image build and start the `svcdesk` service.



\## Task list



1\. Create the FastAPI project files, Dockerfile and Docker Compose service named `svcdesk`.

2\. Add `/health` and JSON error responses for unknown routes and unknown ticket identifiers.

3\. Implement ticket creation with validation, generated IDs, the priority matrix and calculated SLA due times.

4\. Implement reading one ticket, listing tickets and exact `state` and `priority` filters.

5\. Implement the request test clock using `SVCDESK\_TEST\_CLOCK` and `X-Test-Clock`.

6\. Implement the state transitions `ack`, `start`, `resolve`, `close` and `reopen`, including all invalid-transition HTTP 409 responses.

7\. Implement the immutable closed-ticket decision and the seven-day reopen window for resolved tickets.

8\. Implement Europe/Warsaw business-hours SLA calculations, including the closing-time tie rule and daylight-saving offsets.

9\. Implement `GET /tickets/{id}/sla` with acknowledgement breach, resolution breach and pause status.

10\. Run `itsmlab verify 1`, correct every Core failure, then commit, push, tag `lab1/v1` and obtain the final submission receipt.



\## Acceptance target



The completed service must pass every local Core check. The local report should show L1-CORE-1 through L1-CORE-4 as `pass` and L1-CORE-5 as `skip`, because the latter is checked only by the course grader from the existing specs receipt.

