"""Golden acceptance tests — gradient contract (bible/52_golden_expected_gradient_v3_2.md).

Runs the REAL in-memory pipeline over bible/51_test_data_gradient_v3_2.json
and asserts the bible-52 expected render-model values: G1 (two-points anchor,
fully pinned incl. the ROUND_HALF_UP witness 8.4853), G2 (point+vector,
structural), G3 (point+angle, structural), G4 (max_ascent + its identity),
G5 (point-only present-vs-absent), G6 (symbolic point, pinned per-piece
suppression), and E1/E2 (intended errors), plus the full-run, summary,
template-routing, purity, and TeX-level locks.

Expectation sources, per the bible-52 conventions:
- decimal strings and boolean flags for G1/G6 are BYTE-EXACT literals from 52;
- LaTeX fields are pinned as MATHEMATICAL content: the expected strings are
  constructed HERE from bible 52's stated content (e.g. ⟨y³e^{xy},
  y e^{xy}(xy+2)⟩, atan(1/2), atan2(2b, 2a)) rendered via public sympy.latex,
  wrapped in the canonical `\\left\\langle …, \\; … \\right\\rangle` delimiter
  that 52/85 mandate. Bible 52 is the source of truth — no solver output is
  frozen; G2–G5 bind the structural contract only.

This file is separate from tests/test_golden.py and
tests/test_golden_symbolic.py by design: bible 46/47 and 48/49 stay frozen
and this module never touches them. Solver/adapter/template unit behavior is
covered by their own test modules; this is the end-to-end bible lock.
"""

import json
import math
import re
from pathlib import Path

import pytest
import sympy

from solucionario.fileio import load_display_defaults
from solucionario.pipeline import process_document

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIBLE_51_PATH = PROJECT_ROOT / "bible" / "51_test_data_gradient_v3_2.json"

PROCESSED_INFO = {
    "timestamp": "2026-07-11T10:00:00Z",
    "filename": "itson_c3_hw_9012_20260711_100000_extended.json",
    "filename_base": "itson_c3_hw_9012_20260711_100000",
    "naming_mode": "testing",
}

# bible 52 / 85: the generic Spanish render marker for error items. Defined
# locally as the contractual expectation — deliberately NOT imported from
# production code.
GENERIC_ERROR_MESSAGE = "ERROR: no se pudo procesar este ejercicio."

GRADIENT_PIECES = (
    "gradient_evaluated", "magnitude", "unit_vector",
    "directional_derivative", "theta_max",
)

# Structural shapes for the G2-G5 (non-pinned) decimals: 4 dp fixed-point
# scalars and complete canonical-delimiter decimal vectors (bible 52/85).
SCALAR_DECIMAL = re.compile(r"^-?\d+\.\d{4}$")
VECTOR_DECIMAL = re.compile(
    r"^\\left\\langle -?\d+\.\d{4}, \\; -?\d+\.\d{4} \\right\\rangle$"
)

X, Y, A, B = sympy.symbols("x y a b")


def vector(first, second) -> str:
    """bible 52/85 canonical vector delimiter mandate:
    `\\left\\langle … \\right\\rangle` with `, \\;` between components."""
    return (
        r"\left\langle " + sympy.latex(first)
        + r", \; " + sympy.latex(second) + r" \right\rangle"
    )


# --- bible 52 G1 pinned mathematical content ---------------------------------
# ∇f = ⟨y³ e^{xy}, y e^{xy}(xy + 2)⟩; ∇f(P) = ⟨8, 4⟩; |∇f(P)| = 4√5;
# û = ⟨√2/2, √2/2⟩; D_u f = 6√2; theta_max = atan(1/2).
G1_GRADIENT_LATEX = vector(
    Y**3 * sympy.exp(X * Y), Y * (X * Y + 2) * sympy.exp(X * Y)
)
G1_EVALUATED_LATEX = vector(sympy.Integer(8), sympy.Integer(4))
G1_MAGNITUDE_LATEX = sympy.latex(4 * sympy.sqrt(5))
G1_UNIT_VECTOR_LATEX = vector(sympy.sqrt(2) / 2, sympy.sqrt(2) / 2)
G1_DERIVATIVE_LATEX = sympy.latex(6 * sympy.sqrt(2))
G1_THETA_LATEX = sympy.latex(sympy.atan(sympy.Rational(1, 2)))

# --- bible 52 G6 pinned mathematical content ---------------------------------
# ∇f = ⟨2x, 2y⟩; ∇f(P) = ⟨2a, 2b⟩; |∇f(P)| = 2√(a² + b²);
# theta_max = atan2(2b, 2a) (SymPy does not cancel the shared factor).
G6_GRADIENT_LATEX = vector(2 * X, 2 * Y)
G6_EVALUATED_LATEX = vector(2 * A, 2 * B)
G6_MAGNITUDE_LATEX = sympy.latex(2 * sympy.sqrt(A**2 + B**2))
G6_THETA_LATEX = sympy.latex(sympy.atan2(2 * B, 2 * A))


@pytest.fixture(scope="module")
def golden_run():
    input_json = json.loads(BIBLE_51_PATH.read_text(encoding="utf-8"))
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
# G1 — id 1: two-points anchor (Tarea 12 1a, bible 52 fully pinned)
# ---------------------------------------------------------------------------

def test_g1_render_item_fully_pinned(golden_run):
    assert item(golden_run, "1") == {
        "kind": "gradient",
        "exercise_label": "1",
        "show_gradient": True,
        "gradient_latex": G1_GRADIENT_LATEX,
        "show_gradient_evaluated": True,
        "gradient_evaluated_latex": G1_EVALUATED_LATEX,
        "gradient_evaluated_numeric": True,
        "gradient_evaluated_decimal": r"\left\langle 8.0000, \; 4.0000 \right\rangle",
        "show_magnitude": True,
        "magnitude_latex": G1_MAGNITUDE_LATEX,
        "magnitude_numeric": True,
        "magnitude_decimal_string": "8.9443",
        "show_unit_vector": True,
        "unit_vector_latex": G1_UNIT_VECTOR_LATEX,
        "unit_vector_numeric": True,
        "unit_vector_decimal": r"\left\langle 0.7071, \; 0.7071 \right\rangle",
        "show_directional_derivative": True,
        "directional_derivative_latex": G1_DERIVATIVE_LATEX,
        "directional_derivative_numeric": True,
        # THE bible-52 acceptance witness: 6√2 = 8.485281… -> "8.4853"
        # (ROUND_HALF_UP), not the OCR-truncated "8.4852".
        "directional_derivative_decimal_string": "8.4853",
        "show_theta_max": True,
        "theta_max_latex": G1_THETA_LATEX,
        "theta_max_numeric": True,
        "theta_max_decimal_string": "0.4636",
    }


def test_g1_extended_json_raw_values(golden_run):
    results = extended_exercise(golden_run, 1)["results"]
    assert "status" not in results
    assert results["numeric_value"] is None  # every gradient SUCCESS (75)
    gradient = results["gradient"]
    # solution_latex is only the non-rendered mirror (bible 75/52).
    assert results["solution_latex"] == gradient["gradient_latex"]

    # Raw floats derived from bible 52's pinned exact content.
    assert gradient["gradient_evaluated_values"] == [8.0, 4.0]
    assert gradient["magnitude_value"] == pytest.approx(math.sqrt(80), rel=1e-12)
    assert gradient["unit_vector_values"] == pytest.approx(
        [math.sqrt(2) / 2, math.sqrt(2) / 2], rel=1e-12
    )
    assert gradient["directional_derivative_value"] == pytest.approx(
        6 * math.sqrt(2), rel=1e-12
    )
    assert gradient["theta_max_value"] == pytest.approx(math.atan(0.5), rel=1e-12)


# ---------------------------------------------------------------------------
# G2 — id 2: point + vector (bible 52 structural)
# ---------------------------------------------------------------------------

def test_g2_all_six_pieces_present_and_numeric(golden_run):
    g2 = item(golden_run, "2")
    assert g2["kind"] == "gradient"
    assert g2["show_gradient"] is True
    for piece in GRADIENT_PIECES:
        assert g2[f"show_{piece}"] is True
        assert g2[f"{piece}_numeric"] is True
    assert VECTOR_DECIMAL.fullmatch(g2["gradient_evaluated_decimal"])
    assert VECTOR_DECIMAL.fullmatch(g2["unit_vector_decimal"])
    assert SCALAR_DECIMAL.fullmatch(g2["magnitude_decimal_string"])
    assert SCALAR_DECIMAL.fullmatch(g2["directional_derivative_decimal_string"])
    assert SCALAR_DECIMAL.fullmatch(g2["theta_max_decimal_string"])


# ---------------------------------------------------------------------------
# G3 — id 3: point + angle, radians (bible 52 structural)
# ---------------------------------------------------------------------------

def test_g3_all_six_pieces_present_and_numeric(golden_run):
    g3 = item(golden_run, "3")
    assert g3["kind"] == "gradient"
    for piece in GRADIENT_PIECES:
        assert g3[f"show_{piece}"] is True
        assert g3[f"{piece}_numeric"] is True
    # 52: û = ⟨cos(π/4), sin(π/4)⟩ -> decimal ⟨0.7071, 0.7071⟩.
    assert g3["unit_vector_decimal"] == r"\left\langle 0.7071, \; 0.7071 \right\rangle"


# ---------------------------------------------------------------------------
# G4 — id 4: max_ascent identity (bible 52 binding)
# ---------------------------------------------------------------------------

def test_g4_max_ascent_identity(golden_run):
    g4 = item(golden_run, "4")
    assert g4["kind"] == "gradient"
    for piece in GRADIENT_PIECES:
        assert g4[f"show_{piece}"] is True
        assert g4[f"{piece}_numeric"] is True
    # Binding identity (52): D_u f == |∇f(P)| — byte-equal decimal strings.
    assert (
        g4["directional_derivative_decimal_string"]
        == g4["magnitude_decimal_string"]
    )
    gradient = extended_exercise(golden_run, 4)["results"]["gradient"]
    assert gradient["directional_derivative_value"] == pytest.approx(
        gradient["magnitude_value"], rel=1e-12
    )


# ---------------------------------------------------------------------------
# G5 — id 5: point-only (bible 52 present-vs-absent contract)
# ---------------------------------------------------------------------------

def test_g5_point_only_present_vs_absent(golden_run):
    g5 = item(golden_run, "5")
    assert g5["kind"] == "gradient"
    for piece in ("gradient_evaluated", "magnitude", "theta_max"):
        assert g5[f"show_{piece}"] is True
        assert g5[f"{piece}_numeric"] is True
    # Absent pieces: resolved off with contract-closing empty strings (52).
    assert g5["show_unit_vector"] is False
    assert g5["unit_vector_numeric"] is False
    assert g5["unit_vector_latex"] == ""
    assert g5["unit_vector_decimal"] == ""
    assert g5["show_directional_derivative"] is False
    assert g5["directional_derivative_numeric"] is False
    assert g5["directional_derivative_latex"] == ""
    assert g5["directional_derivative_decimal_string"] == ""


def test_g5_direction_pieces_omitted_in_extended_json(golden_run):
    # Not-applicable absence = keys OMITTED upstream (bible 75/52), which is
    # semantically distinct from the symbolic null of G6.
    gradient = extended_exercise(golden_run, 5)["results"]["gradient"]
    for key in (
        "unit_vector_latex", "unit_vector_values",
        "directional_derivative_latex", "directional_derivative_value",
    ):
        assert key not in gradient
    assert gradient["theta_max_value"] is not None  # present AND numeric


# ---------------------------------------------------------------------------
# G6 — id 6: symbolic point (bible 52 fully pinned per-piece suppression)
# ---------------------------------------------------------------------------

def test_g6_render_item_fully_pinned(golden_run):
    assert item(golden_run, "6") == {
        "kind": "gradient",
        "exercise_label": "6",
        "show_gradient": True,
        "gradient_latex": G6_GRADIENT_LATEX,
        "show_gradient_evaluated": True,  # symbolic line stays VISIBLE
        "gradient_evaluated_latex": G6_EVALUATED_LATEX,
        "gradient_evaluated_numeric": False,  # only the decimal resolves off
        "gradient_evaluated_decimal": "",
        "show_magnitude": True,
        "magnitude_latex": G6_MAGNITUDE_LATEX,
        "magnitude_numeric": False,
        "magnitude_decimal_string": "",
        "show_unit_vector": False,  # absent — no direction supplied
        "unit_vector_latex": "",
        "unit_vector_numeric": False,
        "unit_vector_decimal": "",
        "show_directional_derivative": False,
        "directional_derivative_latex": "",
        "directional_derivative_numeric": False,
        "directional_derivative_decimal_string": "",
        "show_theta_max": True,
        "theta_max_latex": G6_THETA_LATEX,
        "theta_max_numeric": False,
        "theta_max_decimal_string": "",
    }


def test_g6_symbolic_nulls_in_extended_json(golden_run):
    results = extended_exercise(golden_run, 6)["results"]
    assert "status" not in results  # symbolic SUCCESS, not error (52)
    assert results["numeric_value"] is None
    gradient = results["gradient"]
    # Applicable-but-symbolic = keys PRESENT with null values (bible 75/52) —
    # distinct from G5's omitted keys.
    assert gradient["gradient_evaluated_values"] is None
    assert gradient["magnitude_value"] is None
    assert gradient["theta_max_value"] is None
    # No direction: û / D_u f are omitted here too.
    assert "unit_vector_latex" not in gradient
    assert "directional_derivative_latex" not in gradient


# ---------------------------------------------------------------------------
# E1 / E2 — ids 7/8: intended errors (bible 52)
# ---------------------------------------------------------------------------

def test_e1_missing_point_is_error(golden_run):
    assert item(golden_run, "7") == {
        "kind": "error", "exercise_label": "7", "message": GENERIC_ERROR_MESSAGE,
    }
    results = extended_exercise(golden_run, 7)["results"]
    assert results["status"] == "error"
    assert "error_message" in results  # internal diagnostic, not the marker
    assert "gradient" not in results


def test_e2_zero_direction_is_error(golden_run):
    assert item(golden_run, "8") == {
        "kind": "error", "exercise_label": "8", "message": GENERIC_ERROR_MESSAGE,
    }
    results = extended_exercise(golden_run, 8)["results"]
    assert results["status"] == "error"
    assert "error_message" in results
    assert "gradient" not in results


# ---------------------------------------------------------------------------
# Full run: all eight cases exactly once, in bible-51 order, without halting
# ---------------------------------------------------------------------------

def test_full_run_all_eight_cases_once_in_order(golden_run):
    items = golden_run["render_model"]["items"]
    assert [i["exercise_label"] for i in items] == [
        "1", "2", "3", "4", "5", "6", "7", "8",
    ]
    assert [i["kind"] for i in items] == ["gradient"] * 6 + ["error"] * 2


def test_processing_summary_counts(golden_run):
    summary = golden_run["extended_json"]["metadata"]["processing_summary"]
    assert summary["total_exercises"] == 8
    assert summary["successful"] == 6
    assert summary["errors"] == 2


def test_document_routes_to_gradient_template(golden_run):
    document = golden_run["render_model"]["document"]
    assert document["template"] == "solucionario_gradientes.tex.j2"


def test_all_successes_share_the_gradient_results_skeleton(golden_run):
    for id in (1, 2, 3, 4, 5, 6):
        results = extended_exercise(golden_run, id)["results"]
        assert results["numeric_value"] is None
        assert results["solution_latex"] == results["gradient"]["gradient_latex"]


# ---------------------------------------------------------------------------
# Extended JSON purity (bible 75): no render-only leakage into exercises
# ---------------------------------------------------------------------------

def test_extended_json_purity_gradient(golden_run):
    def walk(value):
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from walk(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from walk(inner)

    # Walk the EXERCISES (the top-level display blocks legitimately carry
    # authored show_* fields; exercises must carry no render-only fields).
    keys = [str(k) for k in walk(golden_run["extended_json"]["exercises"])]
    assert [k for k in keys if k.startswith("_")] == []
    offenders = [
        k for k in keys
        if k.endswith("_decimal") or k.endswith("_decimal_string")
        or k.endswith("_numeric") or k.startswith("show_")
        or k in {"decimal_string", "units", "exercise_label", "message"}
    ]
    assert offenders == []
    # Gradient gets no quantity/coordinate_system/unit enrichment (91/70).
    for exercise in golden_run["extended_json"]["exercises"]:
        assert "quantity" not in exercise
        assert "coordinate_system" not in exercise


# ---------------------------------------------------------------------------
# TeX (gradient template path): G1 lines in order, G6 without decimal tails,
# omitted pieces fully suppressed, error markers
# ---------------------------------------------------------------------------
# The line-head anchors (\nabla f(x, y) =, \hat{u} =, …) are the template
# labels locked by the approved Batch E template tests; the CONTENT of each
# line and their relative order are the bible-52 contract asserted here.

def test_tex_g1_lines_pinned_and_ordered(golden_run):
    tex = golden_run["tex_string"]
    markers = [
        r"\nabla f(x, y) = " + G1_GRADIENT_LATEX,
        r"\nabla f(P) = " + G1_EVALUATED_LATEX
        + r" = \left\langle 8.0000, \; 4.0000 \right\rangle",
        r"\left| \nabla f(P) \right| = " + G1_MAGNITUDE_LATEX + " = 8.9443",
        r"\hat{u} = " + G1_UNIT_VECTOR_LATEX
        + r" = \left\langle 0.7071, \; 0.7071 \right\rangle",
        r"D_{\hat{u}} f = " + G1_DERIVATIVE_LATEX + " = 8.4853",
        r"\theta_{\max} = " + G1_THETA_LATEX + " = 0.4636",
    ]
    positions = [tex.find(marker) for marker in markers]
    assert all(position >= 0 for position in positions), (markers, positions)
    assert positions == sorted(positions)  # bible 85/52 contract order


def test_tex_g6_symbolic_lines_without_decimal_tails(golden_run):
    tex = golden_run["tex_string"]
    assert r"\nabla f(P) = " + G6_EVALUATED_LATEX in tex
    assert G6_EVALUATED_LATEX + " =" not in tex  # no decimal tail
    assert r"\left| \nabla f(P) \right| = " + G6_MAGNITUDE_LATEX in tex
    assert G6_MAGNITUDE_LATEX + " =" not in tex
    assert r"\theta_{\max} = " + G6_THETA_LATEX in tex
    assert G6_THETA_LATEX + " =" not in tex


def test_tex_omitted_pieces_fully_suppressed(golden_run):
    tex = golden_run["tex_string"]
    # û and D_u f lines exist only for G1-G4; G5 (point-only) and G6 (no
    # direction) render neither the LaTeX nor a decimal tail (52). The
    # trailing space keeps "D_{\hat{u}} f" from matching the û count.
    assert tex.count(r"\hat{u} = ") == 4
    assert tex.count(r"D_{\hat{u}} f = ") == 4
    assert tex.count(r"\theta_{\max} = ") == 6  # all six successes show it


def test_tex_error_markers(golden_run):
    tex = golden_run["tex_string"]
    # E1 and E2 each render exactly one generic Spanish marker (52).
    assert tex.count(GENERIC_ERROR_MESSAGE) == 2
    assert r"\textbf{ 7) }" in tex
    assert r"\textbf{ 8) }" in tex
