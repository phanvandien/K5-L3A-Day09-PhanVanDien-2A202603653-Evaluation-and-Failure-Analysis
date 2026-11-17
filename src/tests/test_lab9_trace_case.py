"""Trace-backed regression case for the first ticket-trust error in C-002."""
import pytest

pytestmark = pytest.mark.student


def test_seeded_regression_c002_detects_first_wrong_step():
    from lab9.trace_case import investigate

    broken = investigate("seeded_regression", "C-002", 11)["trial"]
    fixed = investigate("fixed", "C-002", 11)["trial"]
    first_wrong = next(i for i, event in enumerate(broken["events"], 1)
                       if event.get("kind") == "model_override")
    assert first_wrong == 3
    assert broken["snapshot"]["refund_vnd"] == 20000
    assert fixed["snapshot"]["refund_vnd"] == 0
