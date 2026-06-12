"""Tests for the in-memory pipeline (M7B2).

Runs the REAL bible/46 edge-case document end to end (validate -> clean ->
solve -> aggregate -> enrich -> Extended JSON -> adapter -> Jinja2) and locks:
golden-shaped render items, the revised enrichment gates, cleaner field
wiring with original-string preservation, Extended JSON purity, input
immutability, document-level hard stop, and the no-writes scope.
"""

import ast
import copy
import json
from pathlib import Path

import pytest

from solucionario import pipeline
from solucionario.fileio import load_display_defaults
from solucionario.pipeline import infer_coordinate_system, process_document
from solucionario.render.adapter import ERROR_MESSAGE
from solucionario.validation import DocumentValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIBLE_46_PATH = PROJECT_ROOT / "bible" / "46_test_data_integral_edge_cases_v3_2.json"

DEFAULTS = load_display_defaults()

PROCESSED_INFO = {
    "timestamp": "2026-06-12T10:00:00Z",
    "filename": "itson_c3_test_9001_extended.json",
    "filename_base": "itson_c3_test_9001",
    "naming_mode": "testing",
}


def load_46() -> dict:
    return json.loads(BIBLE_46_PATH.read_text(encoding="utf-8"))


def run(input_json: dict) -> dict:
    return process_document(
        input_json, processed_info=PROCESSED_INFO, display_defaults=DEFAULTS
    )


def make_document(exercises: list[dict]) -> dict:
    return {
        "metadata": {"course": "Calculus 3", "assignment": {"type": "hw", "number": 1}},
        "exercises": exercises,
    }


def items_by_label(result: dict) -> dict:
    return {item["exercise_label"]: item for item in result["render_model"]["items"]}


def exercise_by_id(result: dict, id) -> dict:
    matches = [e for e in result["extended_json"]["exercises"] if e.get("id") == id]
    assert len(matches) == 1, f"expected exactly one exercise with id {id}"
    return matches[0]


@pytest.fixture(scope="module")
def result46():
    return run(load_46())


# ---------------------------------------------------------------------------
# Full bible-46 run: shape and golden-shaped render items
# ---------------------------------------------------------------------------

def test_returns_exactly_the_three_key_shape(result46):
    assert set(result46) == {"extended_json", "render_model", "tex_string"}
    assert isinstance(result46["tex_string"], str)
    assert "PRUEBA 9001" in result46["tex_string"]  # type "test" -> Prueba
    assert r"\end{document}" in result46["tex_string"]


def test_ex1_standard_with_inferred_area(result46):
    item = items_by_label(result46)["1"]
    assert item["kind"] == "standard"
    assert item["quantity_label"] == "A"
    assert item["units"] == "u^2"
    assert item["decimal_string"] == "1.0000"
    exercise = exercise_by_id(result46, 1)
    assert exercise["quantity"] == "A"  # enrichment made inference explicit
    assert exercise["coordinate_system"] == "cartesian"


def test_ex5_component_group_with_total_one(result46):
    item = items_by_label(result46)["5"]
    assert item["kind"] == "component_group"
    assert item["total_latex"] == "1"
    assert item["total_decimal_string"] == "1.0000"
    assert item["operation_decimal_string"] == "0.5000 + 0.5000"


def test_ex6_output_group(result46):
    item = items_by_label(result46)["6"]
    assert item["kind"] == "output_group"
    assert [o["output_label"] for o in item["outputs"]] == ["Resultado 1", "Resultado 2"]


def test_ex7_override_reaches_render_model(result46):
    item = items_by_label(result46)["7"]
    assert item["quantity_label"] == "Q"
    assert item["units"] == "C"
    assert item["decimal_string"] == "4.00"
    assert item["show_symbolic"] is False
    assert item["show_numeric"] is True
    # The underlying exercise field stays the inferred "R" — the Q label is
    # display-only (display_override.quantity_label).
    assert exercise_by_id(result46, 7)["quantity"] == "R"


def test_ex9_errors_and_ex10_still_processes(result46):
    items = items_by_label(result46)
    assert items["9"] == {
        "kind": "error", "exercise_label": "9", "message": ERROR_MESSAGE,
    }
    assert items["10"]["kind"] == "standard"
    assert items["10"]["quantity_label"] == "R"
    assert items["10"]["decimal_string"] == "0.3333"

    summary = result46["extended_json"]["metadata"]["processing_summary"]
    assert summary["total_exercises"] == 12
    assert summary["successful"] == 11
    assert summary["errors"] == 1


# ---------------------------------------------------------------------------
# Enrichment gates (revised M28 rules)
# ---------------------------------------------------------------------------

def test_ex9_function_failure_gate(result46):
    # Function "2x" cannot be cleaned: quantity must NOT be inferred from a
    # broken function, but coordinate_system (vars only) IS inferred.
    exercise = exercise_by_id(result46, 9)
    assert exercise["results"]["status"] == "error"
    assert "quantity" not in exercise
    assert exercise["coordinate_system"] == "cartesian"


def test_bound_failure_keeps_partial_enrichment():
    exercise = {
        "id": 1, "type": "integral", "function": "1",
        "integrals": [
            {"var": "y", "lower": "0", "upper": "2y"},  # implicit mult: fails
            {"var": "x", "lower": "0", "upper": "1"},
        ],
    }
    result = run(make_document([exercise]))
    processed = exercise_by_id(result, 1)
    assert processed["results"]["status"] == "error"  # bound failure -> error
    assert processed["quantity"] == "A"  # function cleaned fine: inferred
    assert processed["coordinate_system"] == "cartesian"  # vars readable
    assert items_by_label(result)["1"]["kind"] == "error"


def test_validation_failure_skips_all_enrichment():
    exercise = {"id": 1, "type": "integral", "function": "1"}  # integrals missing
    result = run(make_document([exercise]))
    processed = exercise_by_id(result, 1)
    assert processed["results"]["status"] == "error"
    assert "quantity" not in processed
    assert "coordinate_system" not in processed


def test_explicit_quantity_and_coordinate_system_win():
    exercise = {
        "id": 1, "type": "integral", "quantity": "M", "coordinate_system": "polar",
        "function": "1",
        "integrals": [
            {"var": "y", "lower": "0", "upper": "1"},
            {"var": "x", "lower": "0", "upper": "1"},
        ],
    }
    processed = exercise_by_id(run(make_document([exercise])), 1)
    assert processed["quantity"] == "M"  # not the inferred "A"
    assert processed["coordinate_system"] == "polar"  # not "cartesian"


@pytest.mark.parametrize(
    "variables, expected",
    [
        (["x", "y"], "cartesian"),
        (["x", "y", "z"], "cartesian"),
        (["r", "theta"], "polar"),
        (["r", "theta", "z"], "cylindrical"),
        (["rho", "phi", "theta"], "spherical"),
        (["u", "v"], None),
        (["x"], None),
    ],
)
def test_infer_coordinate_system_table(variables, expected):
    exercise = {
        "integrals": [{"var": v, "lower": "0", "upper": "1"} for v in variables]
    }
    assert infer_coordinate_system(exercise) == expected


def test_cylindrical_inference_through_full_pipeline():
    exercise = {
        "id": 2, "type": "integral", "quantity": "V", "function": "r",
        "integrals": [
            {"var": "z", "lower": "0", "upper": "1"},
            {"var": "r", "lower": "0", "upper": "1"},
            {"var": "theta", "lower": "0", "upper": "2*pi"},
        ],
    }
    processed = exercise_by_id(run(make_document([exercise])), 2)
    assert processed["coordinate_system"] == "cylindrical"
    assert "status" not in processed["results"]  # passive: still solved


def test_unknown_variable_set_leaves_field_absent():
    exercise = {
        "id": 3, "type": "integral", "function": "1",
        "integrals": [
            {"var": "u", "lower": "0", "upper": "1"},
            {"var": "v", "lower": "0", "upper": "1"},
        ],
    }
    processed = exercise_by_id(run(make_document([exercise])), 3)
    assert "coordinate_system" not in processed
    assert processed["quantity"] == "A"  # quantity gate independent


# ---------------------------------------------------------------------------
# Cleaner field wiring and original-string preservation
# ---------------------------------------------------------------------------

def test_ex8_cleans_function_and_bounds_but_persists_originals(result46):
    exercise = exercise_by_id(result46, 8)
    assert "status" not in exercise["results"]  # ln/sin^2/exp(1) all solved
    assert exercise["function"] == "ln(x) + sin^2(y)"  # authored string kept
    assert exercise["integrals"][0]["upper"] == "pi/2"
    assert exercise["integrals"][1]["upper"] == "exp(1)"


def test_non_math_fields_are_never_cleaned_or_changed(result46):
    original = load_46()
    extended = result46["extended_json"]
    assert extended["display_default"] == original["display_default"]
    assert extended["display_integral"] == original["display_integral"]
    assert extended["metadata"]["course"] == "Calculus 3"
    exercise4 = exercise_by_id(result46, 4)
    assert exercise4["quantity"] == "M"  # explicit label untouched
    assert exercise4["display_override"] == {"units_override": "kg"}
    assert [b["var"] for b in exercise4["integrals"]] == ["z", "y", "x"]


# ---------------------------------------------------------------------------
# Purity, immutability, hard stop, scope locks
# ---------------------------------------------------------------------------

def test_extended_json_purity_after_full_pipeline(result46):
    forbidden = {
        "decimal_string", "total_decimal_string", "operation_decimal_string",
        "units", "exercise_label", "output_label", "message",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)

    keys = list(walk(result46["extended_json"]))
    assert [k for k in keys if str(k).startswith("_")] == []
    assert [k for k in keys if k in forbidden] == []


def test_input_json_is_not_mutated():
    document = load_46()
    snapshot = copy.deepcopy(document)
    run(document)
    assert document == snapshot


def test_document_failure_raises_before_any_solving(monkeypatch):
    monkeypatch.setattr(
        pipeline, "solve_integral",
        lambda exercise: pytest.fail("solver must not be called on a hard stop"),
    )
    with pytest.raises(DocumentValidationError):
        run({"metadata": {"course": "Calculus 3"}, "exercises": []})


def test_no_writes_during_full_run(tmp_path):
    outputs = PROJECT_ROOT / "outputs"
    listing_before = sorted(p.name for p in outputs.iterdir())
    tex_before = set(PROJECT_ROOT.rglob("*.tex"))

    run(load_46())

    assert sorted(p.name for p in outputs.iterdir()) == listing_before
    assert set(PROJECT_ROOT.rglob("*.tex")) == tex_before


def test_pipeline_imports_no_filesystem_or_subprocess():
    tree = ast.parse(Path(pipeline.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported == {"time", "solucionario"}  # no subprocess/os/pathlib/shutil
