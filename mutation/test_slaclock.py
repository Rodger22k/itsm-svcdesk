# ai-generated: 90% - OpenAI Codex drafted boundary-focused mutation tests; the student ran and reviewed the official mutant report
"""Behavioural tests for the course SLA clock module.

The suite deliberately checks documented boundaries instead of inspecting the
implementation, so it remains valid for behaviourally equivalent rewrites.
"""

from datetime import datetime, timedelta

import pytest

import slaclock


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (1, 3, "P3"),
        (2, 1, "P2"),
        (2, 2, "P3"),
        (2, 3, "P4"),
        (3, 1, "P3"),
        (3, 2, "P4"),
        (3, 3, "P4"),
    ],
)
def test_priority_matrix(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency) == expected


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 1, "P2"),
        (1, 3, "P2"),
        (2, 2, "P2"),
        (2, 3, "P2"),
        (3, 1, "P2"),
        (3, 2, "P2"),
        (3, 3, "P2"),
    ],
)
def test_vip_priority_never_below_p2(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency, vip=True) == expected


@pytest.mark.parametrize("bad", [0, 4, -1, 2.0, True, "1", None])
def test_priority_rejects_invalid_impact(bad):
    with pytest.raises(ValueError):
        slaclock.priority_of(bad, 2)


@pytest.mark.parametrize("bad", [0, 4, -1, 2.0, True, "1", None])
def test_priority_rejects_invalid_urgency(bad):
    with pytest.raises(ValueError):
        slaclock.priority_of(2, bad)


@pytest.mark.parametrize(
    ("priority", "expected"),
    [
        ("P1", (15, 240)),
        ("P2", (60, 480)),
        ("P3", (240, 1440)),
        ("P4", (480, 4320)),
    ],
)
def test_targets(priority, expected):
    assert slaclock.targets(priority) == expected


@pytest.mark.parametrize("priority", ["p1", " P1", "P1 ", "P0", "P5", ""])
def test_targets_require_an_exact_known_priority(priority):
    with pytest.raises(ValueError):
        slaclock.targets(priority)


@pytest.mark.parametrize(
    ("elapsed", "target", "expected"),
    [
        (0, 15, "ok"),
        (11, 15, "ok"),
        (12, 15, "warning"),
        (15, 15, "warning"),
        (16, 15, "breached"),
        (74, 100, "ok"),
        (75, 100, "warning"),
        (74, 99, "ok"),
        (100, 100, "warning"),
        (101, 100, "breached"),
        (0, 1, "ok"),
        (1, 1, "warning"),
        (2, 1, "breached"),
    ],
)
def test_sla_state_boundaries(elapsed, target, expected):
    assert slaclock.sla_state(elapsed, target) == expected


@pytest.mark.parametrize(("elapsed", "target"), [(-1, 10), (0, 0), (0, -1)])
def test_sla_state_rejects_invalid_durations(elapsed, target):
    with pytest.raises(ValueError):
        slaclock.sla_state(elapsed, target)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 1, 5, 7, 59, 59), False),  # Monday
        (datetime(2026, 1, 5, 8, 0), True),
        (datetime(2026, 1, 5, 8, 30), True),
        (datetime(2026, 1, 5, 15, 59, 59), True),
        (datetime(2026, 1, 5, 16, 0), False),
        (datetime(2026, 1, 9, 8, 0), True),  # Friday
        (datetime(2026, 1, 10, 10, 0), False),  # Saturday
        (datetime(2026, 1, 11, 10, 0), False),  # Sunday
    ],
)
def test_business_time_boundaries(moment, expected):
    assert slaclock.is_business_time(moment) is expected


@pytest.mark.parametrize(
    ("start", "minutes", "expected"),
    [
        (datetime(2026, 1, 5, 10, 15, 42, 900), 0, datetime(2026, 1, 5, 10, 15)),
        (datetime(2026, 1, 5, 7, 30), 0, datetime(2026, 1, 5, 8, 0)),
        (datetime(2026, 1, 5, 16, 0), 0, datetime(2026, 1, 6, 8, 0)),
        (datetime(2026, 1, 10, 10, 0), 0, datetime(2026, 1, 12, 8, 0)),
        (datetime(2026, 1, 9, 16, 30), 0, datetime(2026, 1, 12, 8, 0)),
        (datetime(2026, 1, 5, 7, 30), 60, datetime(2026, 1, 5, 9, 0)),
        (datetime(2026, 1, 5, 8, 0), 480, datetime(2026, 1, 5, 16, 0)),
        (datetime(2026, 1, 5, 15, 59), 1, datetime(2026, 1, 5, 16, 0)),
        (datetime(2026, 1, 5, 15, 59), 2, datetime(2026, 1, 6, 8, 1)),
        (datetime(2026, 1, 9, 15, 0), 120, datetime(2026, 1, 12, 9, 0)),
    ],
)
def test_add_business_minutes(start, minutes, expected):
    assert slaclock.add_business_minutes(start, minutes) == expected


def test_add_business_minutes_rejects_negative_value():
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(datetime(2026, 1, 5, 8, 0), -1)


def test_add_business_minutes_accepts_due_date_at_maximum_span():
    start = datetime(2026, 1, 5, 8, 0)
    assert slaclock.add_business_minutes(start, 263 * 480) == datetime(2027, 1, 6, 16, 0)


def test_add_business_minutes_rejects_due_date_beyond_maximum_span():
    start = datetime(2026, 1, 5, 8, 0)
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(start, 263 * 480 + 1)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 5, 9, 0), 0),
        (datetime(2026, 1, 5, 8, 0), datetime(2026, 1, 5, 16, 0), 480),
        (datetime(2026, 1, 5, 7, 0), datetime(2026, 1, 5, 8, 0), 0),
        (datetime(2026, 1, 5, 7, 0), datetime(2026, 1, 5, 9, 0), 60),
        (datetime(2026, 1, 5, 15, 0), datetime(2026, 1, 5, 17, 0), 60),
        (datetime(2026, 1, 9, 15, 0), datetime(2026, 1, 12, 9, 0), 120),
        (datetime(2026, 1, 10, 8, 0), datetime(2026, 1, 11, 16, 0), 0),
        (datetime(2026, 1, 5, 8, 0, 59), datetime(2026, 1, 5, 8, 1, 1), 1),
    ],
)
def test_business_minutes_between(start, end, expected):
    assert slaclock.business_minutes_between(start, end) == expected


def test_business_minutes_between_rejects_reverse_interval():
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(
            datetime(2026, 1, 5, 9, 1), datetime(2026, 1, 5, 9, 0)
        )


def test_business_minutes_between_maximum_span_boundary():
    start = datetime(2026, 1, 5, 0, 0)
    assert slaclock.business_minutes_between(start, start + timedelta(days=366)) == 125_760
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, start + timedelta(days=367))


def test_business_minutes_between_returns_an_integer_and_ignores_microseconds():
    result = slaclock.business_minutes_between(
        datetime(2026, 1, 5, 8, 0, 59, 999_999),
        datetime(2026, 1, 5, 8, 1),
    )
    assert result == 1
    assert type(result) is int


@pytest.mark.parametrize(
    ("start", "minutes"),
    [
        (datetime(2026, 1, 5, 8, 0), 0),
        (datetime(2026, 1, 5, 7, 0), 75),
        (datetime(2026, 1, 5, 15, 45), 30),
        (datetime(2026, 1, 9, 15, 30), 120),
        (datetime(2026, 1, 10, 12, 0), 480),
    ],
)
def test_add_and_between_are_inverse(start, minutes):
    due = slaclock.add_business_minutes(start, minutes)
    assert slaclock.business_minutes_between(start, due) == minutes


@pytest.mark.parametrize(
    ("priority", "breached", "reopens", "expected"),
    [
        ("P1", False, 0, 1),
        ("P1", False, 1, 1),
        ("P1", False, 2, 2),
        ("P1", True, 0, 3),
        ("P1", True, 2, 3),
        ("P2", False, 0, 1),
        ("P2", False, 2, 2),
        ("P2", True, 0, 2),
        ("P2", True, 2, 3),
        ("P3", False, 0, 0),
        ("P3", False, 2, 1),
        ("P3", True, 0, 1),
        ("P3", True, 2, 2),
        ("P4", False, 0, 0),
        ("P4", False, 2, 1),
        ("P4", True, 0, 1),
        ("P4", True, 2, 2),
    ],
)
def test_escalation_tiers(priority, breached, reopens, expected):
    assert slaclock.escalation_tier(priority, breached, reopens) == expected


@pytest.mark.parametrize("priority", ["p1", "P0", "P5", ""])
def test_escalation_rejects_unknown_priority(priority):
    with pytest.raises(ValueError):
        slaclock.escalation_tier(priority, False, 0)


def test_escalation_rejects_negative_reopen_count():
    with pytest.raises(ValueError):
        slaclock.escalation_tier("P2", False, -1)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("90m", 90),
        ("1m", 1),
        ("4h", 240),
        ("1h30m", 90),
        ("2d", 2880),
        ("1d4h", 1680),
        ("1d0h5m", 1445),
        ("  1h30m  ", 90),
        ("60m", 60),
        ("0h60m", 60),
        ("0d60m", 60),
        ("24h", 1440),
        ("1d24h", 2880),
    ],
)
def test_parse_duration_valid_values(text, expected):
    assert slaclock.parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "0m",
        "0h",
        "0d",
        "1.5h",
        "30m1h",
        "-5m",
        "1 h",
        "1H",
        "m",
        "1h60m",
        "1d60m",
        "1m1m",
        "1d2d",
        "1h30m extra",
    ],
)
def test_parse_duration_rejects_invalid_values(text):
    with pytest.raises(ValueError):
        slaclock.parse_duration(text)
