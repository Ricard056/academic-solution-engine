"""Golden acceptance tests — symbolic contract (bible/49_golden_expected_symbolic_v3_2.md).

Runs the REAL in-memory pipeline over
bible/48_test_data_symbolic_v3_2.json and asserts the bible-49 expected
render-model values field-for-field for Ex 1 and Ex 2 (symbolic-only
successes), Ex 3 (component group with a symbolic member — an INTENDED group
ERROR, same acceptance semantics as bible-47's Ex 9), and Ex 4/Ex 5
(divergence guards that must remain ERRORs despite the symbolic-success
contract).

This file is separate from tests/test_golden.py by design: bible 46/47 stay
the frozen Phase 1 acceptance set and this module never touches them.
"""

import json
from pathlib import Path

import pytest

from solucionario.fileio import load_display_defaults
from solucionario.pipeline import process_document
from solucionario.render.adapter import ERROR_MESSAGE

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIBLE_48_PATH = PROJECT_ROOT / "bible" / "48_test_data_symbolic_v3_2.json"

PROCESSED_INFO = {
    "timestamp": "2026-07-06T10:00:00Z",
    "filename": "itson_c3_test_9002_20260706_100000_extended.json",
    "filename_base": "itson_c3_test_9002_20260706_100000",
    "naming_mode": "testing",
}


@pytest.fixture(scope="module")
def golden_run():
    input_json = json.loads(BIBLE_48_PATH.read_text(encoding="utf-8"))
    return process_document(
        input_json,
        processed_info=PROCESSED_INFO,
        display_defaults=load_display_defaults(),
    )


def item(golden_run, label: str) -> dict:
    matches = [
        i for i in golden_run["render_model"]["items"] if i["exercise_label"] == label
    ]
    assert len(matches) == 1
    return matches[0]


def extended_exercise(golden_run, id) -> dict:
    matches = [
        e for e in golden_run["extended_json"]["exercises"] if e.get("id") == id
    ]
    assert len(matches) == 1
    return matches[0]


# ---------------------------------------------------------------------------
# Ex 1 — S1: standard symbolic success, parameters in the bounds (bible 49)
# ---------------------------------------------------------------------------

def test_ex1_symbolic_standard(golden_run):
    ex1 = item(golden_run, "1")
    assert ex1["kind"] == "standard"
    assert ex1["exercise_label"] == "1"
    assert ex1["quantity_label"] == "A"  # inferred: 2 integrals + function "1"
    assert ex1["units"] == "u^2"
    assert ex1["solution_latex"] == "a b"
    assert ex1["show_numeric"] is False  # RESOLVED off despite config true
    assert ex1["decimal_string"] == ""
    assert ex1["show_input"] is True
    assert ex1["show_symbolic"] is True
    assert ex1["show_quantity"] is True
    # Source Extended JSON: null is a SUCCESS, not a dropped/zeroed field.
    assert extended_exercise(golden_run, 1)["results"]["numeric_value"] is None


# ---------------------------------------------------------------------------
# Ex 2 — standard symbolic success, parameter in the function, 1D (bible 49)
# ---------------------------------------------------------------------------

def test_ex2_symbolic_standard(golden_run):
    ex2 = item(golden_run, "2")
    assert ex2["kind"] == "standard"
    assert ex2["exercise_label"] == "2"
    assert ex2["quantity_label"] == "R"  # 1D never infers A/V
    assert ex2["units"] == "u"
    assert ex2["solution_latex"] == r"\frac{k}{3}"
    assert ex2["show_numeric"] is False
    assert ex2["decimal_string"] == ""
    assert ex2["show_input"] is True
    assert ex2["show_symbolic"] is True
    assert ex2["show_quantity"] is True
    assert extended_exercise(golden_run, 2)["results"]["numeric_value"] is None


# ---------------------------------------------------------------------------
# Ex 3 — S2: component group with a symbolic member (INTENDED ERROR)
# ---------------------------------------------------------------------------

def test_ex3_component_symbolic_member_is_one_error_item(golden_run):
    assert item(golden_run, "3") == {
        "kind": "error", "exercise_label": "3", "message": ERROR_MESSAGE,
    }


# ---------------------------------------------------------------------------
# Ex 4 / Ex 5 — divergence guards (must REMAIN errors)
# ---------------------------------------------------------------------------

def test_ex4_divergence_guard_remains_error(golden_run):
    assert item(golden_run, "4") == {
        "kind": "error", "exercise_label": "4", "message": ERROR_MESSAGE,
    }


def test_ex5_divergence_guard_remains_error(golden_run):
    assert item(golden_run, "5") == {
        "kind": "error", "exercise_label": "5", "message": ERROR_MESSAGE,
    }


# ---------------------------------------------------------------------------
# Acceptance rule 4: the full 48 run completes without halting
# ---------------------------------------------------------------------------

def test_full_run_completes(golden_run):
    items = golden_run["render_model"]["items"]
    assert [i["exercise_label"] for i in items] == ["1", "2", "3", "4", "5"]
    assert [i["kind"] for i in items] == [
        "standard", "standard", "error", "error", "error",
    ]


# ---------------------------------------------------------------------------
# Extended JSON purity (bible 75)
# ---------------------------------------------------------------------------

def test_extended_json_purity_symbolic(golden_run):
    forbidden = {
        "decimal_string", "total_decimal_string", "operation_decimal_string",
        "units", "exercise_label", "output_label", "message",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from walk(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from walk(inner)

    keys = list(walk(golden_run["extended_json"]))
    assert [k for k in keys if str(k).startswith("_")] == []
    assert [k for k in keys if k in forbidden] == []
