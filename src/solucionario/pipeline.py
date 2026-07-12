"""Pipeline orchestration — M7B2: pure in-memory processing.

process_document() runs the Phase 1 stages in order (bible 90):
    Validate -> Expression Cleaner -> Integral Solver (per-exercise)
    -> Component Aggregation -> Extended JSON -> Render Adapter -> Jinja2
and returns {"extended_json", "render_model", "tex_string"} WITHOUT writing
anything. Output writing, outputs/ management, pdflatex, and the CLI are
M7B3/M7B4 — this module imports no subprocess/os/pathlib (test-locked).

Per-exercise behavior (bible 90 matrix + approved enrichment gates):
- validate_exercise failure -> error_result, NO enrichment (the exercise may
  be structurally incomplete).
- validation passed -> the processed copy keeps the ORIGINAL authored
  function/bound strings forever (bible 75 reusability); cleaned strings are
  transient solver/enrichment inputs only.
- coordinate_system enrichment depends only on integrals[].var, so it is
  applied even when cleaning later fails. Explicit value wins; a variable set
  outside the bible-70 table leaves the field absent. The field remains
  computationally passive — nothing downstream reads it.
- quantity enrichment requires a successfully cleaned function (2/3 integrals
  + cleaned "1" -> A/V, else R). Explicit value wins; a broken function never
  feeds inference.
- any CleanerError (function or bound) -> error_result with the cleaner's
  message; processing continues with the next exercise. Solver failures are
  already error results (solve_integral never raises).

Phase 2A (bible 91): _process_exercise dispatches by exercise type. Gradient
exercises take a parallel path — clean (function, each point/initial_point/
final_point/vector entry, angle) -> solve_gradient — with NO enrichment:
quantity, coordinate_system, and units never apply to gradient (91/70).
Component Aggregation is integral-only; gradient exercises are standard
items (bible 65) and pass through it untouched. Mixed gradient+integral
documents are a document-level hard stop inside validate_document (91).

Document-level validation failure raises DocumentValidationError before any
exercise work: hard stop, nothing produced (bible 55/90).
"""

import time

from solucionario.aggregation import aggregate_components
from solucionario.cleaner import CleanerError, clean_expression
from solucionario.extended_json import build_extended_json
from solucionario.render.adapter import build_render_model
from solucionario.render.latex import render_tex
from solucionario.solvers.base import error_result
from solucionario.solvers.gradient import solve_gradient
from solucionario.solvers.integral import solve_integral
from solucionario.validation import validate_document, validate_exercise

# bible 70: variable-name sets -> coordinate system label (passive metadata).
_COORDINATE_SYSTEMS = (
    ({"x", "y"}, "cartesian"),
    ({"x", "y", "z"}, "cartesian"),
    ({"r", "theta"}, "polar"),
    ({"r", "theta", "z"}, "cylindrical"),
    ({"rho", "phi", "theta"}, "spherical"),
)


def process_document(
    input_json: dict, *, processed_info: dict, display_defaults: dict
) -> dict:
    """Run the full in-memory Phase 1 pipeline over one loaded input document.

    Returns {"extended_json", "render_model", "tex_string"}. Never mutates
    input_json and never touches the filesystem (render_tex reads templates
    only).
    """
    validate_document(input_json)  # hard stop BEFORE any processing

    started = time.perf_counter()
    processed = [_process_exercise(exercise) for exercise in input_json["exercises"]]
    aggregated = aggregate_components(processed)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    extended = build_extended_json(
        input_json,
        aggregated,
        processed_info=processed_info,
        processing_time_ms=elapsed_ms,
    )
    render_model = build_render_model(extended, display_defaults)
    return {
        "extended_json": extended,
        "render_model": render_model,
        "tex_string": render_tex(render_model),
    }


def infer_coordinate_system(exercise: dict) -> str | None:
    """bible 70 variable-set table; None when the set is not in the table."""
    integrals = exercise.get("integrals")
    if not isinstance(integrals, list):
        return None
    variables = {bound.get("var") for bound in integrals if isinstance(bound, dict)}
    for table_set, system in _COORDINATE_SYSTEMS:
        if variables == table_set:
            return system
    return None


def _infer_quantity(cleaned_function: str, integrals: list) -> str:
    """bible 70/90: 2/3 integrals + cleaned function "1" -> A/V, else R."""
    if cleaned_function == "1":
        if len(integrals) == 2:
            return "A"
        if len(integrals) == 3:
            return "V"
    return "R"


def _process_exercise(exercise: dict) -> dict:
    """One exercise: validate -> enrich (gated) -> clean -> solve. Never raises."""
    processed = dict(exercise)  # shallow copy; input_json is never mutated

    message = validate_exercise(exercise)
    if message is not None:
        processed["results"] = error_result(message)
        return processed  # no enrichment: possibly structurally incomplete

    if exercise["type"] == "gradient":
        return _process_gradient_exercise(exercise, processed)

    # coordinate_system needs only integrals[].var (validated readable), so
    # it is inferred even if cleaning fails below. Explicit value wins.
    if processed.get("coordinate_system") is None:
        inferred = infer_coordinate_system(exercise)
        if inferred is not None:
            processed["coordinate_system"] = inferred

    failure = None
    cleaned_function = None
    try:
        cleaned_function = clean_expression(str(exercise["function"]))
    except CleanerError as exc:
        failure = exc

    # quantity: only a successfully cleaned function may feed inference.
    if processed.get("quantity") is None and cleaned_function is not None:
        processed["quantity"] = _infer_quantity(cleaned_function, exercise["integrals"])

    cleaned_integrals = None
    if failure is None:
        try:
            cleaned_integrals = [
                {
                    **bound,
                    "lower": clean_expression(str(bound["lower"])),
                    "upper": clean_expression(str(bound["upper"])),
                }
                for bound in exercise["integrals"]
            ]
        except CleanerError as exc:
            failure = exc

    if failure is not None:
        processed["results"] = error_result(str(failure))
    else:
        # Cleaned strings are transient solver input only; `processed` keeps
        # the authored strings (bible 75 reusability).
        processed["results"] = solve_integral(
            {**exercise, "function": cleaned_function, "integrals": cleaned_integrals}
        )
    return processed


# Gradient math fields cleaned entry-wise (bible 60, gradient cleaner scope).
_GRADIENT_COORDINATE_FIELDS = ("point", "initial_point", "final_point", "vector")


def _process_gradient_exercise(exercise: dict, processed: dict) -> dict:
    """Gradient path (bible 91): clean -> solve. Never raises.

    No enrichment: quantity, coordinate_system, and units never apply to
    gradient (bible 91/70). `processed` keeps the ORIGINAL authored strings
    (bible 75 reusability); cleaned strings are transient solver input only.
    Any CleanerError in any math field -> error_result, run continues.
    """
    cleaned = {}
    try:
        cleaned["function"] = clean_expression(str(exercise["function"]))
        for field in _GRADIENT_COORDINATE_FIELDS:
            if exercise.get(field) is not None:
                cleaned[field] = [
                    clean_expression(str(entry)) for entry in exercise[field]
                ]
        if exercise.get("angle") is not None:
            cleaned["angle"] = clean_expression(str(exercise["angle"]))
    except CleanerError as exc:
        processed["results"] = error_result(str(exc))
        return processed

    processed["results"] = solve_gradient({**exercise, **cleaned})
    return processed
