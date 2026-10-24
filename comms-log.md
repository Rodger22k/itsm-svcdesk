---
lab4_comms:
  awareness: 2026-10-12T05:06:56Z
  detection: 2026-10-12T05:06:19Z
  classification: 2026-10-12T05:07:30Z
  nis2:
    early_warning_due: 2026-10-13T05:06:56Z
    notification_due: 2026-10-15T05:06:56Z
    notification_sent: 2026-10-12T08:00:00Z
    final_report_due: 2026-11-12T08:00:00Z
  ksc:
    early_warning_due: 2026-10-13T05:06:19Z
    notification_due: 2026-10-15T05:06:19Z
    notification_sent: 2026-10-12T08:05:00Z
    final_report_due: 2026-11-12T08:05:00Z
  dora:
    initial_due: 2026-10-12T09:07:30Z
    initial_sent: 2026-10-12T08:10:00Z
    intermediate_due: 2026-10-15T08:10:00Z
    intermediate_sent: 2026-10-13T08:10:00Z
    final_due: 2026-11-13T08:10:00Z
  log:
    - {at: 2026-10-12T08:00:00Z, to: CSIRT designated under NIS2, what: significant-incident notification with scope and mitigations}
    - {at: 2026-10-12T08:05:00Z, to: competent Polish KSC authority, what: incident notification with detection and recovery clocks}
    - {at: 2026-10-12T08:10:00Z, to: financial supervisory authority, what: DORA initial major-incident notification}
    - {at: 2026-10-13T08:10:00Z, to: financial supervisory authority, what: DORA intermediate report with validated technical causes}
---
<!-- ai-generated: 85% - ChatGPT calculated the regulatory deadlines and drafted the explanations from the student's incident timestamps -->

# Communications log: the regulators' clocks

## The three instants you defend

For NIS2, awareness is 05:06:56 UTC, when the on-call engineer acknowledged the P1 ticket and had enough information to treat the event as significant. For KSC, detection is the alert instant, 05:06:19 UTC, because that is when monitoring first identified the incident. For DORA, classification is 05:07:30 UTC, after the shipping-latency, advertisement-error and resource signals showed that the incident met the assumed major ICT-related incident criteria.

NIS2 deadlines are measured from awareness: the early warning is due after 24 elapsed hours and the notification after 72 hours. KSC uses the same intervals but starts them at detection. The selected NIS2 and KSC notifications are sent on the same UTC morning as the incident, well before both deadlines, and each final report is due one calendar month after its own notification.

DORA's initial deadline is four hours after classification, 09:07:30 UTC. Classification occurred within 24 hours of awareness and this four-hour result is earlier than the awareness-plus-24-hours cap. The initial report is sent at 08:10:00 UTC. Its submission starts the 72-hour intermediate-report clock, and the final DORA report is due one calendar month after the intermediate report sent on 13 October.

## The log

| Time in UTC | Recipient | Communication |
|---|---|---|
| 2026-10-12T08:00:00Z | CSIRT designated under NIS2 | Significant-incident notification describing the checkout impact, current status and mitigation. |
| 2026-10-12T08:05:00Z | Competent Polish KSC authority | Incident notification with the detection, acknowledgement and recovery timestamps. |
| 2026-10-12T08:10:00Z | Financial supervisory authority | DORA initial report identifying the event as a major ICT-related incident. |
| 2026-10-13T08:10:00Z | Financial supervisory authority | DORA intermediate report with the validated advertisement, shipping and email-service causes. |
