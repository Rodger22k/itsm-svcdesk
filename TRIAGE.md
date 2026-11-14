---
lab5_triage:
  image: ghcr.io/rodger22k/itsm-svcdesk@sha256:66908b6ad42fabd443cd0a63b706e5f0fa418fa892db07c5c82f8bccdc9701e2
  sarif_receipt: 367
---
<!-- ai-generated: 85% - OpenAI Codex drafted the evidence table and interpretation; the student executed the scans, verified the findings, applied the fixes, and reviewed the conclusions -->
# Triage

This document records the findings produced against my service by the five scanners in the receipted SARIF set. Each row represents one tool and rule pair found outside `lab5-canary/`.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| grype | GHSA-6w46-j5rx-g56g-pytest | fix | Grype reported pytest 8.3.5 in `/requirements.txt`; I upgraded the root dependency pin to the fixed pytest 9.0.3 release in commit `571e522`. |
| osv-scanner | CVE-2025-71176 | fix | OSV-Scanner produced duplicate findings for pytest 8.3.5 at `file:///src/requirements.txt`; the corresponding root pin was upgraded to pytest 9.0.3. |
| semgrep | dockerfile.security.missing-user.missing-user | fix | Semgrep reported the missing non-root user at `Dockerfile:20`; the image now creates and selects user `svcdesk` and grants it access to `/app` and `/data`. |
| trivy | CVE-2025-71176 | fix | Trivy reported pytest 8.3.5 at `requirements.txt:3`; the package was upgraded to fixed version 9.0.3 and the current dependency and image jobs pass. |

## Bake-off

The receipted canary contained nine labelled defects. Gitleaks detected two defects, produced one false positive and missed seven, which gave precision 0.6667, recall 0.2222 and F1 0.3333. Its result confirms that it is useful as a specialised secret detector, but it cannot be treated as a general security scanner. Grype detected two dependency defects with no false positives, giving precision 1.0, recall 0.2222 and F1 0.3636. OSV-Scanner produced the same confusion matrix as Grype: two true positives, no false positives and seven false negatives. Their perfect precision is valuable, but their low recall follows from their narrow focus on vulnerable packages rather than application code.

Semgrep achieved the strongest overall result: five true positives, two false positives and four false negatives. Its precision was 0.7143, recall 0.5556 and F1 0.625. Trivy was second by F1, with three true positives, one false positive, six false negatives, precision 0.75, recall 0.3333 and F1 0.4615. Trivy covered more than one type of problem, but its coverage remained lower than Semgrep's. I was surprised that the dependency scanners achieved perfect precision while still missing seven of nine defects; this demonstrates that precision alone does not describe the practical usefulness of a detector.

If I had to add one of these detectors as a blocking code gate, I would select Semgrep because it had the highest recall and F1 score. I would first baseline or tune its two false-positive rules so that unrelated reports did not stop every build. Grype and OSV-Scanner remain useful dependency gates because their precision was 1.0, while gitleaks should remain a separate specialised gate for credentials. In practice, the results support combining several focused detectors rather than expecting one tool to cover every weakness class.

Two labelled defects were missed by every detector: the SSRF defect in `lab5-canary/app/webhook_relay.py` and the secret in `lab5-canary/config/jwt_secret.py`. They belong to different weakness classes, but neither was expressed in a form recognised by the enabled signatures and rules. They show that syntax patterns and known package metadata cannot replace contextual review. Finally, every recall value here should be treated as an upper bound for real software. The canary defects were deliberately seeded, isolated and made easier for scanners to recognise, whereas production defects are usually mixed with application logic, indirect data flows and project-specific abstractions. Real-world recall would therefore probably be lower.
