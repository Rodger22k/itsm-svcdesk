# ai-generated: 95% - ChatGPT implemented the published Lab 2 metric rules R-01 through R-18
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


UTC = timezone.utc


class MetricsValidationError(ValueError):
    """Raised when a metrics request or event log violates METRIC-SPEC.md."""


def _invalid(message: str) -> MetricsValidationError:
    return MetricsValidationError(message)


def _instant(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise _invalid(f"{field} must be an RFC 3339 instant")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise _invalid(f"{field} must be an RFC 3339 instant") from error
    if parsed.tzinfo is None:
        raise _invalid(f"{field} must include a timezone offset")
    return parsed.astimezone(UTC)


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise _invalid(f"{field} must be a non-empty string")
    return value


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise _invalid(f"{field} must be an array of non-empty strings")
    return value


def _round_seconds(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _round_rate(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _seconds(later: datetime, earlier: datetime) -> Decimal:
    return Decimal(str((later - earlier).total_seconds()))


def _duration(later: datetime, earlier: datetime) -> tuple[Decimal, bool]:
    value = _seconds(later, earlier)
    if value < 0:
        return Decimal(0), True
    return value, False


def _median(values: list[Decimal]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        value = ordered[middle]
    else:
        value = (ordered[middle - 1] + ordered[middle]) / Decimal(2)
    return _round_seconds(value)


def _validate_and_index(events_value: Any) -> dict[str, Any]:
    if not isinstance(events_value, list):
        raise _invalid("events must be an array")

    events: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()

    for position, raw_event in enumerate(events_value):
        if not isinstance(raw_event, dict):
            raise _invalid(f"events[{position}] must be an object")
        event_id = raw_event.get("event_id")
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 64:
            raise _invalid(f"events[{position}].event_id must contain 1 to 64 characters")
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)
        events.append(raw_event)

    commits: dict[str, dict[str, Any]] = {}
    deployments: dict[str, dict[str, Any]] = {}
    incident_phases: dict[str, dict[str, dict[str, Any]]] = {}

    for event in events:
        event_id = event["event_id"]
        event_type = event.get("type")
        if event_type not in {"commit", "deployment", "incident"}:
            raise _invalid(f"event {event_id} has an unsupported type")
        at = _instant(event.get("at"), f"event {event_id}.at")

        if event_type == "commit":
            sha = _non_empty_string(event.get("sha"), f"event {event_id}.sha")
            if sha in commits:
                raise _invalid(f"commit sha {sha} is not unique")
            branch = event.get("branch")
            if not isinstance(branch, str):
                raise _invalid(f"event {event_id}.branch must be a string")
            change_id = event.get("change_id")
            reverts = event.get("reverts")
            if reverts is None:
                _non_empty_string(change_id, f"event {event_id}.change_id")
            else:
                _non_empty_string(reverts, f"event {event_id}.reverts")
                if change_id is not None:
                    raise _invalid(f"event {event_id}.change_id must be null on a revert")
            commits[sha] = {**event, "_at": at}

        elif event_type == "deployment":
            deployment_id = _non_empty_string(
                event.get("deployment_id"), f"event {event_id}.deployment_id"
            )
            if deployment_id in deployments:
                raise _invalid(f"deployment_id {deployment_id} is not unique")
            environment = event.get("environment")
            if not isinstance(environment, str):
                raise _invalid(f"event {event_id}.environment must be a string")
            if event.get("outcome") not in {"success", "failure"}:
                raise _invalid(f"event {event_id}.outcome must be success or failure")
            _string_list(event.get("commits"), f"event {event_id}.commits")
            if type(event.get("unplanned")) is not bool:
                raise _invalid(f"event {event_id}.unplanned must be a boolean")
            caused_by = event.get("caused_by")
            if caused_by is not None:
                _non_empty_string(caused_by, f"event {event_id}.caused_by")
            deployments[deployment_id] = {**event, "_at": at}

        else:
            incident_id = _non_empty_string(
                event.get("incident_id"), f"event {event_id}.incident_id"
            )
            phase = event.get("phase")
            if phase not in {"opened", "resolved"}:
                raise _invalid(f"event {event_id}.phase must be opened or resolved")
            _string_list(event.get("deployments"), f"event {event_id}.deployments")
            phases = incident_phases.setdefault(incident_id, {})
            if phase in phases:
                raise _invalid(f"incident {incident_id} has more than one {phase} event")
            phases[phase] = {**event, "_at": at}

    incident_ids = set(incident_phases)
    for sha, commit in commits.items():
        reverts = commit.get("reverts")
        if reverts is not None and reverts not in commits:
            raise _invalid(f"commit {sha} reverts unknown sha {reverts}")

    for deployment_id, deployment in deployments.items():
        for sha in deployment["commits"]:
            if sha not in commits:
                raise _invalid(f"deployment {deployment_id} references unknown sha {sha}")
        caused_by = deployment.get("caused_by")
        if caused_by is not None and caused_by not in incident_ids:
            raise _invalid(f"deployment {deployment_id} references unknown incident {caused_by}")

    for incident_id, phases in incident_phases.items():
        if "resolved" in phases and "opened" not in phases:
            raise _invalid(f"incident {incident_id} resolved without being opened")
        for phase_event in phases.values():
            for deployment_id in phase_event["deployments"]:
                if deployment_id not in deployments:
                    raise _invalid(
                        f"incident {incident_id} references unknown deployment {deployment_id}"
                    )

    change_cache: dict[str, str] = {}

    def change_for(sha: str, trail: set[str] | None = None) -> str:
        if sha in change_cache:
            return change_cache[sha]
        trail = set() if trail is None else trail
        if sha in trail:
            raise _invalid("revert references form a cycle")
        trail.add(sha)
        commit = commits[sha]
        if commit.get("reverts") is None:
            change_id = commit["change_id"]
        else:
            change_id = change_for(commit["reverts"], trail)
        trail.remove(sha)
        change_cache[sha] = change_id
        return change_id

    for sha in commits:
        change_for(sha)

    return {
        "events": events,
        "commits": commits,
        "deployments": deployments,
        "incident_phases": incident_phases,
        "change_for": change_for,
    }


def compute_metrics(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise _invalid("request body must be a JSON object")
    window = payload.get("window")
    if not isinstance(window, dict):
        raise _invalid("window must be an object")
    if "from" not in window or "to" not in window:
        raise _invalid("window.from and window.to are required")
    window_from = _instant(window["from"], "window.from")
    window_to = _instant(window["to"], "window.to")
    if window_to <= window_from:
        raise _invalid("window.to must be after window.from")
    if "events" not in payload:
        raise _invalid("events is required")

    indexed = _validate_and_index(payload["events"])
    commits: dict[str, dict[str, Any]] = indexed["commits"]
    deployments: dict[str, dict[str, Any]] = indexed["deployments"]
    incident_phases: dict[str, dict[str, dict[str, Any]]] = indexed["incident_phases"]
    change_for = indexed["change_for"]

    production = [
        deployment
        for deployment in deployments.values()
        if deployment["environment"] == "production"
        and window_from <= deployment["_at"] < window_to
    ]
    production.sort(key=lambda item: (item["_at"], item["deployment_id"]))
    successful = [item for item in production if item["outcome"] == "success"]
    failed = [item for item in production if item["outcome"] == "failure"]
    rework = [
        item
        for item in production
        if item["unplanned"] is True and item.get("caused_by") is not None
    ]

    lead_times: list[Decimal] = []
    delivered_shas: set[str] = set()
    negative_lead_time_pairs = 0
    for deployment in successful:
        for sha in deployment["commits"]:
            if sha in delivered_shas:
                continue
            delivered_shas.add(sha)
            duration, negative = _duration(deployment["_at"], commits[sha]["_at"])
            lead_times.append(duration)
            negative_lead_time_pairs += int(negative)

    off_main_shas = {
        sha
        for deployment in production
        for sha in deployment["commits"]
        if commits[sha]["branch"] != "main"
    }

    incidents: list[dict[str, Any]] = []
    for incident_id, phases in incident_phases.items():
        opened = phases.get("opened")
        if opened is None:
            continue
        covered = set(opened["deployments"])
        if "resolved" in phases:
            covered.update(phases["resolved"]["deployments"])
        incidents.append(
            {
                "incident_id": incident_id,
                "opened": opened["_at"],
                "resolved": phases.get("resolved", {}).get("_at"),
                "deployments": covered,
            }
        )

    recovery_times: list[Decimal] = []
    open_failures = 0
    for deployment in failed:
        covering = [
            incident
            for incident in incidents
            if deployment["deployment_id"] in incident["deployments"]
        ]
        covering.sort(key=lambda item: (item["opened"], item["incident_id"]))
        incident = covering[0] if covering else None
        if incident is None or incident["resolved"] is None:
            open_failures += 1
            continue
        duration, _ = _duration(incident["resolved"], deployment["_at"])
        recovery_times.append(duration)

    overlapping_incident_pairs = 0
    for left_index, left in enumerate(incidents):
        left_end = left["resolved"] if left["resolved"] is not None else window_to
        for right in incidents[left_index + 1 :]:
            right_end = right["resolved"] if right["resolved"] is not None else window_to
            if left["opened"] < right_end and right["opened"] < left_end:
                overlapping_incident_pairs += 1

    changes = {change_for(sha) for sha in commits}
    first_commit: dict[str, datetime] = {}
    for sha, commit in commits.items():
        change_id = change_for(sha)
        current = first_commit.get(change_id)
        if current is None or commit["_at"] < current:
            first_commit[change_id] = commit["_at"]

    first_change_delivery: dict[str, datetime] = {}
    for deployment in successful:
        for sha in deployment["commits"]:
            change_id = change_for(sha)
            first_change_delivery.setdefault(change_id, deployment["_at"])

    true_lead_times: list[Decimal] = []
    for change_id, deployed_at in first_change_delivery.items():
        duration, _ = _duration(deployed_at, first_commit[change_id])
        true_lead_times.append(duration)

    deployment_count = len(production)
    failed_count = len(failed)
    window_days = _seconds(window_to, window_from) / Decimal(86400)
    frequency = _round_rate(Decimal(deployment_count) / window_days)
    change_fail_rate = (
        None if deployment_count == 0 else _round_rate(Decimal(failed_count) / deployment_count)
    )
    rework_rate = (
        None if deployment_count == 0 else _round_rate(Decimal(len(rework)) / deployment_count)
    )

    return {
        "spec_version": "1.0.0",
        "window": {"from": window["from"], "to": window["to"]},
        "deployment_frequency_per_day": frequency,
        "change_lead_time_seconds_p50": _median(lead_times),
        "failed_deployment_recovery_time_seconds_p50": _median(recovery_times),
        "change_fail_rate": change_fail_rate,
        "deployment_rework_rate": rework_rate,
        "counts": {
            "deployments": deployment_count,
            "successful_deployments": len(successful),
            "failed_deployments": failed_count,
            "recovered_failures": len(recovery_times),
            "open_failures": open_failures,
            "rework_deployments": len(rework),
            "lead_time_pairs": len(lead_times),
            "changes": len(changes),
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": sum(not item["commits"] for item in production),
            "commits_never_on_main": len(off_main_shas),
            "revert_chains_collapsed": sum(
                commit.get("reverts") is not None for commit in commits.values()
            ),
            "overlapping_incident_pairs": overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered": len(first_change_delivery),
            "true_change_lead_time_seconds_p50": _median(true_lead_times),
        },
    }
