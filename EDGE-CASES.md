---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 90% - ChatGPT drafted the explanations from the published rules and computed results -->

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- What the log contains: Three commit and deployment pairs have a commit timestamp later than the successful production deployment that carried it.
- What a default definition would have done: A simple duration calculation would return negative lead times, while some implementations might silently discard those inconvenient observations.
- Why the rule is defensible: Clamping the durations to zero retains evidence that the commits were delivered while preventing clock skew from creating impossible negative performance values.

## E2 - a revert of a revert

- What the log contains: Two commits are reverts, and one of them reverts another revert, so both resolve transitively to the original change identifier.
- What a default definition would have done: Treating each revert as a separate change would inflate the change count and misrepresent one chain of corrective work as three independent changes.
- Why the rule is defensible: Following the complete revert chain preserves the identity of the original unit of work and avoids manufacturing extra delivery throughput.

## E3 - a hotfix that never touched `main`

- What the log contains: Four distinct commits on branches other than `main` were carried by production deployments during the measurement window.
- What a default definition would have done: A main-branch-only calculation would omit genuine production work and report incomplete lead-time and delivery data.
- Why the rule is defensible: Production deployment evidence is stronger than branch naming, especially for emergency hotfixes intentionally shipped from another branch.

## E4 - a deployment with zero linked commits

- What the log contains: Four production deployments in the window contain an empty `commits` array, including successful and failed deployments.
- What a default definition would have done: An implementation focused only on commit pairs might discard these deployments from every denominator and overstate operational performance.
- Why the rule is defensible: A real production deployment still consumes delivery capacity and can fail even when its source-control linkage is missing.

## E5 - a deployment that failed and never recovered

- What the log contains: One failed production deployment has no covering incident with a recorded resolution, so its recovery duration remains unknown.
- What a default definition would have done: Inventing a recovery at the end of the window or treating it as zero would distort the recovery median and conceal unfinished work.
- Why the rule is defensible: Excluding the unknown duration while counting the open failure makes the missing recovery visible without fabricating an event that never occurred.

## E6 - overlapping incidents

- What the log contains: The incident intervals produce eleven unordered overlapping pairs when open incidents are measured through the end of the observation window.
- What a default definition would have done: Merging intersecting incidents would erase their individual relationship to failed deployments and alter the per-deployment recovery calculation.
- Why the rule is defensible: Keeping incident intervals separate preserves causality and permits each failed deployment to receive the recovery instant of its selected covering incident.

## Gaming demonstration

The demonstration improves `change_fail_rate` under rule R-14 from 0.190476 to 0.166667. It adds six successful production deployments with no linked commits, increasing the denominator while leaving the eight failures unchanged. It also removes commit links from the existing successful production deployments, which R-19 explicitly permits, so delivery of the original work becomes measurably worse: reported base changes delivered fall from 65 to 0. A team rewarded only for a lower change fail rate could be encouraged to split or record harmless empty deployments while weakening traceability between code and production. The deployment or platform team would appear to perform better on the dashboard, while product teams, auditors and customers would bear the cost of missing delivery evidence and undelivered work.
