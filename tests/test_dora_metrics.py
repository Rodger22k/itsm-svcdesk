# ai-generated: 95% - ChatGPT drafted tests for the published Lab 2 metric contract
import json
from copy import deepcopy
from pathlib import Path

import pytest

from dora_metrics import MetricsValidationError, compute_metrics


ROOT = Path(__file__).resolve().parents[1]
WINDOW = {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}


def practice_events():
    return [
        json.loads(line)
        for line in (ROOT / "fixtures" / "events-practice.jsonl").read_text().splitlines()
        if line.strip()
    ]


def event(event_id, event_type, at, **fields):
    return {"event_id": event_id, "type": event_type, "at": at, **fields}


def test_empty_log_has_zero_counts_and_null_ratios():
    result = compute_metrics({"window": WINDOW, "events": []})
    assert result["deployment_frequency_per_day"] == 0.0
    assert result["change_lead_time_seconds_p50"] is None
    assert result["failed_deployment_recovery_time_seconds_p50"] is None
    assert result["change_fail_rate"] is None
    assert result["deployment_rework_rate"] is None
    assert all(value == 0 for value in result["counts"].values())
    assert all(value == 0 for value in result["anomalies"].values())


def test_practice_fixture_matches_published_answer():
    expected = json.loads((ROOT / "fixtures" / "metrics-practice.json").read_text())
    actual = compute_metrics({"window": WINDOW, "events": practice_events()})
    assert actual == expected


def test_event_order_does_not_change_result():
    events = practice_events()
    forward = compute_metrics({"window": WINDOW, "events": events})
    backward = compute_metrics({"window": WINDOW, "events": list(reversed(events))})
    assert backward == forward


def test_duplicate_event_ids_use_first_occurrence_once():
    events = practice_events()
    original = compute_metrics({"window": WINDOW, "events": events})
    duplicated = compute_metrics({"window": WINDOW, "events": events + deepcopy(events)})
    assert duplicated == original


def test_empty_window_is_rejected():
    with pytest.raises(MetricsValidationError):
        compute_metrics(
            {
                "window": {"from": "2026-09-01T00:00:00Z", "to": "2026-09-01T00:00:00Z"},
                "events": [],
            }
        )


def test_missing_window_is_rejected():
    with pytest.raises(MetricsValidationError):
        compute_metrics({"events": []})


def test_missing_events_is_rejected():
    with pytest.raises(MetricsValidationError):
        compute_metrics({"window": WINDOW})


def test_unknown_revert_reference_is_rejected():
    bad_commit = event(
        "c1",
        "commit",
        "2026-09-02T00:00:00Z",
        sha="sha-1",
        branch="main",
        change_id=None,
        reverts="missing-sha",
    )
    with pytest.raises(MetricsValidationError):
        compute_metrics({"window": WINDOW, "events": [bad_commit]})


def test_non_production_deployment_is_ignored():
    commit = event(
        "c1",
        "commit",
        "2026-09-02T00:00:00Z",
        sha="sha-1",
        branch="main",
        change_id="CHG-1",
        reverts=None,
    )
    deployment = event(
        "d1",
        "deployment",
        "2026-09-03T00:00:00Z",
        deployment_id="DEP-1",
        environment="staging",
        outcome="success",
        commits=["sha-1"],
        unplanned=False,
        caused_by=None,
    )
    result = compute_metrics({"window": WINDOW, "events": [commit, deployment]})
    assert result["counts"]["deployments"] == 0
    assert result["ground_truth"]["changes_delivered"] == 0


def test_window_is_half_open():
    deployment = event(
        "d1",
        "deployment",
        WINDOW["to"],
        deployment_id="DEP-1",
        environment="production",
        outcome="success",
        commits=[],
        unplanned=False,
        caused_by=None,
    )
    result = compute_metrics({"window": WINDOW, "events": [deployment]})
    assert result["counts"]["deployments"] == 0


def test_revert_chain_collapses_to_original_change():
    commits = [
        event(
            "c1", "commit", "2026-09-02T00:00:00Z", sha="sha-1", branch="main",
            change_id="CHG-1", reverts=None,
        ),
        event(
            "c2", "commit", "2026-09-03T00:00:00Z", sha="sha-2", branch="main",
            change_id=None, reverts="sha-1",
        ),
        event(
            "c3", "commit", "2026-09-04T00:00:00Z", sha="sha-3", branch="main",
            change_id=None, reverts="sha-2",
        ),
    ]
    result = compute_metrics({"window": WINDOW, "events": commits})
    assert result["counts"]["changes"] == 1
    assert result["anomalies"]["revert_chains_collapsed"] == 2


def test_failure_without_covering_incident_remains_open():
    deployment = event(
        "d1",
        "deployment",
        "2026-09-03T00:00:00Z",
        deployment_id="DEP-1",
        environment="production",
        outcome="failure",
        commits=[],
        unplanned=False,
        caused_by=None,
    )
    result = compute_metrics({"window": WINDOW, "events": [deployment]})
    assert result["counts"]["failed_deployments"] == 1
    assert result["counts"]["open_failures"] == 1
    assert result["failed_deployment_recovery_time_seconds_p50"] is None
