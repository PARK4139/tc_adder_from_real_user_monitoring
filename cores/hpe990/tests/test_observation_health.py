"""Liveness cannot imply successful recent observation."""

import pytest

from cores.hpe990.functions.semantic_ram import observation_health


@pytest.mark.parametrize("age,state", [(9999, "observing"), (10000, "observing"), (10001, "stale")])
def test_freshness_boundary(age, state):
    result = observation_health(
        {"active": True, "observation": {"observed_unix_ms": 50000}}, 50000 + age
    )
    assert result["observation_health"]["state"] == state
    assert result["sampling_healthy"] == (state == "observing")


@pytest.mark.parametrize(
    "status,state",
    [
        ({"active": False}, "stopped"),
        ({"active": True}, "starting"),
        ({"active": True, "observation": {"observed_unix_ms": 5, "error": "failed"}}, "error"),
    ],
)
def test_unhealthy_states(status, state):
    result = observation_health(status, 100)
    assert not result["sampling_healthy"]
    assert result["observation_health"]["state"] == state


def test_recovery_and_interval_threshold():
    status = {"active": True, "interval_ms": 5000, "observation": {"observed_unix_ms": 1}}
    assert not observation_health(status, 20002)["sampling_healthy"]
    status["observation"]["observed_unix_ms"] = 20002
    result = observation_health(status, 20003)
    assert result["sampling_healthy"]
    assert result["observation_health"]["stale_after_ms"] == 20000
