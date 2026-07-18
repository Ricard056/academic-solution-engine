"""Render Adapter: build_render_model(extended_json, display_defaults).

Bridges canonical Extended JSON (bible 75) to the closed render model of
bible 85. The adapter owns display-merge usage, decimal strings, labels,
quantity/unit resolution, grouping, ordering, and error surfacing — and is
deliberately explicit and boring: every ambiguity is resolved here so the
template never makes a decision.

The adapter must NOT compute math: total_latex, operation_latex and
total_value are copied from results.component (written upstream by the
Component Aggregation stage); operation_decimal_string is formatted from the
ordered member numeric values. No SymPy, no solver, no aggregation imports
(guarded by tests/test_architecture.py). It never mutates Extended JSON and
never writes formatted values back into it.

Error items carry ONE generic Spanish message — solver error_message and
validate_group() diagnostics are internal and never exposed in the render
model (bible 90: no detailed classification).

Numeric-Availability Resolution (bible 85, Phase 1.1): show_numeric is a
RESOLVED visibility flag, author_requested_numeric AND numeric_value_exists.
A null results.numeric_value (symbolic-only success, bible 75) forces
show_numeric to False and decimal_string to "" regardless of the merged
display config, per standard item / per output member. Component groups
never reach this: aggregation already refuses a group with a null-numeric
member, so it has no results.component and collapses to one error item.

Phase 2A (bible 85/91): the "gradient" render item generalizes that rule PER
PIECE — show_<piece> = author flag AND piece present in results.gradient
(symbolic never hides the line); <piece>_numeric = show_<piece> AND value
not null (gates only the decimal tail). Every gradient field is sourced from
results.gradient, never top-level numeric_value/solution_latex; gradient is
unitless with no quantity_label and declares no show_input/problem_latex
(authored show_input is inert by construction). The document block carries
the bible-85 "template" routing field, derived from the (validated
single-solver) document's exercise types before any grouping.
"""

from solucionario.display import resolve_display, resolve_group_display
from solucionario.ids import (
    MODE_COMPONENT,
    MODE_OUTPUT,
    MODE_STANDARD,
    group_exercises,
    group_mode,
)
from solucionario.render.formatting import (
    format_decimal,
    format_operation_decimal_string,
    format_vector_decimal,
)
from solucionario.render.labels import (
    derive_units,
    exercise_label,
    output_label,
    resolve_quantity_label,
)
from solucionario.validation import validate_group

ERROR_MESSAGE = "ERROR: no se pudo procesar este ejercicio."

# bible 85/92 (Phase 2B-M): the adapter's emittable render-item kind set is
# closed and DECLARED. The renderer's FRAGMENT_REGISTRY must cover it exactly
# (mandatory architecture test; drift fails the suite).
EMITTABLE_KINDS = frozenset(
    {"standard", "component_group", "output_group", "gradient", "error"}
)

# bible 85, Document Label Derivation (authoritative maps).
ASSIGNMENT_TYPE_LABELS = {
    "hw": "Tarea",
    "exam": "Examen",
    "quiz": "Quiz",
    "test": "Prueba",
    "project": "Proyecto",
}
COURSE_LABELS = {"Calculus 3": "Cálculo III"}

SUBTITLE = "Solucionario"  # fixed Phase 1 string (bible 85)

# bible 85, Template routing (by document solver; single-solver documents).
INTEGRAL_TEMPLATE = "solucionario_integrales.tex.j2"
GRADIENT_TEMPLATE = "solucionario_gradientes.tex.j2"

# Bible-50 values used only if the provided defaults template is incomplete.
_FALLBACKS = {
    "show_input": True,
    "show_symbolic": True,
    "show_numeric": True,
    "show_quantity": True,
    "decimal_places": 4,
    "show_component_quantity": True,
    "show_component_symbolic": True,
    "show_component_operation": True,
    "show_component_total": True,
    "show_gradient": True,
    "show_gradient_evaluated": True,
    "show_magnitude": True,
    "show_unit_vector": True,
    "show_directional_derivative": True,
    "show_theta_max": True,
}


def build_render_model(extended_json: dict, display_defaults: dict) -> dict:
    """Canonical Extended JSON + hardcoded defaults -> closed render model."""
    exercises = extended_json.get("exercises") or []
    document = _document(extended_json.get("metadata") or {})
    # Template routing field (bible 85): derived from the document's exercise
    # type set BEFORE grouping/sorting — documents are single-solver (91).
    document["template"] = _document_template(exercises)

    items: list[dict] = []
    for _key, members in group_exercises(exercises):
        items.extend(_group_items(extended_json, display_defaults, members))
    return {"document": document, "items": items}


# ---------------------------------------------------------------------------
# Document block (bible 85, Document Label Derivation)
# ---------------------------------------------------------------------------

def _format_number(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _document(metadata: dict) -> dict:
    assignment = metadata.get("assignment") or {}
    type_token = assignment.get("type")
    type_label = ASSIGNMENT_TYPE_LABELS.get(type_token, str(type_token))
    assignment_label = f"{type_label} {_format_number(assignment.get('number'))}"
    course = metadata.get("course")
    return {
        "title": assignment_label.upper(),
        "subtitle": SUBTITLE,
        "course": COURSE_LABELS.get(course, course),
        "assignment_label": assignment_label,
    }


def _document_template(exercises: list) -> str:
    """bible 85: gradient documents use the gradient template; anything else
    defaults to the integral template (Phase 1 back-compatible). The document
    is validated single-solver (91), so any gradient exercise decides."""
    for exercise in exercises:
        if isinstance(exercise, dict) and exercise.get("type") == "gradient":
            return GRADIENT_TEMPLATE
    return INTEGRAL_TEMPLATE


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def _group_items(extended_json, display_defaults, members) -> list[dict]:
    """Render items for one (id, id_letter) group, in final order."""
    label = exercise_label(members[0])

    if validate_group(members) is not None:
        return [_error_item(label)]  # diagnostics stay internal (bible 90)

    mode = group_mode(members)
    if mode == MODE_COMPONENT:
        if any(_failed(m) for m in members):
            return [_error_item(label)]  # one member down -> whole group errors
        return [_component_group_item(extended_json, display_defaults, members, label)]
    if mode == MODE_OUTPUT:
        if any(_failed(m) for m in members):
            return [_error_item(label)]  # bible 90 collapse applies to outputs too
        return [_output_group_item(extended_json, display_defaults, members, label)]
    if mode == MODE_STANDARD:
        items = []
        for member in members:
            if _failed(member):
                items.append(_error_item(exercise_label(member)))
            elif member.get("type") == "gradient":
                items.append(_gradient_item(extended_json, display_defaults, member))
            else:
                items.append(_standard_item(extended_json, display_defaults, member))
        return items
    return [_error_item(label)]  # unclassifiable: defensive


def _failed(exercise: dict) -> bool:
    results = exercise.get("results")
    return not isinstance(results, dict) or results.get("status") == "error"


def _setting(settings: dict, key: str):
    return settings.get(key, _FALLBACKS[key])


def _error_item(label: str) -> dict:
    return {"kind": "error", "exercise_label": label, "message": ERROR_MESSAGE}


def _resolve_numeric(settings: dict, numeric_value, decimal_places: int) -> tuple[bool, str]:
    """Numeric-Availability Resolution (bible 85): show_numeric is resolved
    visibility (author_requested AND numeric_value_exists); a null
    numeric_value forces show_numeric False and decimal_string "" instead of
    formatting (format_decimal would raise on None)."""
    if numeric_value is None:
        return False, ""
    return _setting(settings, "show_numeric"), format_decimal(numeric_value, decimal_places)


def _standard_item(extended_json, display_defaults, exercise) -> dict:
    settings = resolve_display(display_defaults, extended_json, exercise)
    results = exercise["results"]
    quantity_label = resolve_quantity_label(exercise)
    show_numeric, decimal_string = _resolve_numeric(
        settings, results["numeric_value"], _setting(settings, "decimal_places")
    )
    return {
        "kind": "standard",
        "exercise_label": exercise_label(exercise),
        "quantity_label": quantity_label,
        "show_input": _setting(settings, "show_input"),
        "show_symbolic": _setting(settings, "show_symbolic"),
        "show_numeric": show_numeric,
        "show_quantity": _setting(settings, "show_quantity"),
        "problem_latex": results["problem_latex"],
        "solution_latex": results["solution_latex"],
        "decimal_string": decimal_string,
        "units": derive_units(quantity_label, settings),
    }


# The five valued gradient pieces (bible 85), in render-item order:
# (piece, raw value key in results.gradient, render decimal field, vector?).
_GRADIENT_PIECES = (
    ("gradient_evaluated", "gradient_evaluated_values",
     "gradient_evaluated_decimal", True),
    ("magnitude", "magnitude_value", "magnitude_decimal_string", False),
    ("unit_vector", "unit_vector_values", "unit_vector_decimal", True),
    ("directional_derivative", "directional_derivative_value",
     "directional_derivative_decimal_string", False),
    ("theta_max", "theta_max_value", "theta_max_decimal_string", False),
)


def _gradient_item(extended_json, display_defaults, exercise) -> dict:
    """Gradient render item (bible 85): every field sourced from
    results.gradient — never top-level numeric_value/solution_latex. No
    units, no quantity_label, no show_input/problem_latex (authored
    show_input is inert by construction).

    Per-piece Numeric-Availability Resolution: show_<piece> = author flag
    AND piece present (a symbolic value never hides the line);
    <piece>_numeric = show_<piece> AND value not null (gates only the
    decimal tail). Closed contract: absent pieces keep every declared field,
    with show/numeric False and LaTeX/decimal "".
    """
    settings = resolve_display(display_defaults, extended_json, exercise)
    decimal_places = _setting(settings, "decimal_places")
    gradient = exercise["results"]["gradient"]

    item = {
        "kind": "gradient",
        "exercise_label": exercise_label(exercise),
        # gradient_latex is always present: the author flag alone gates it.
        "show_gradient": bool(_setting(settings, "show_gradient")),
        "gradient_latex": gradient["gradient_latex"],
    }
    for piece, value_key, decimal_field, is_vector in _GRADIENT_PIECES:
        latex_key = f"{piece}_latex"
        present = latex_key in gradient  # omitted key = not applicable (75)
        show = bool(_setting(settings, f"show_{piece}")) and present
        value = gradient.get(value_key)
        numeric = show and value is not None

        item[f"show_{piece}"] = show
        item[latex_key] = gradient[latex_key] if present else ""
        item[f"{piece}_numeric"] = numeric
        if numeric:
            item[decimal_field] = (
                format_vector_decimal(value, decimal_places)
                if is_vector
                else format_decimal(value, decimal_places)
            )
        else:
            item[decimal_field] = ""  # closed contract: empty, never missing
    return item


def _component_group_item(extended_json, display_defaults, members, label) -> dict:
    # Group-level resolution for ALL fields of a component group, including
    # component-line decimals and flags: per-member display_override is not
    # honored inside component groups in Phase 1 (bible 85).
    settings = resolve_group_display(display_defaults, extended_json)
    decimal_places = _setting(settings, "decimal_places")
    quantity_label = resolve_quantity_label(members[0])  # uniform (validated)
    units = derive_units(quantity_label, settings)

    component = members[0]["results"].get("component")
    if not isinstance(component, dict):
        return _error_item(label)  # aggregation did not run; unsafe to render

    components = [
        {
            "id_component": member["id_component"],
            "quantity_label": quantity_label,
            "units": units,
            "show_component_quantity": _setting(settings, "show_component_quantity"),
            "show_numeric": _setting(settings, "show_numeric"),
            "problem_latex": member["results"]["problem_latex"],
            "solution_latex": member["results"]["solution_latex"],
            "decimal_string": format_decimal(
                member["results"]["numeric_value"], decimal_places
            ),
        }
        for member in members  # already ordered by id_component (ids)
    ]

    return {
        "kind": "component_group",
        "exercise_label": label,
        "quantity_label": quantity_label,
        "units": units,
        "show_quantity": _setting(settings, "show_quantity"),
        "show_numeric": _setting(settings, "show_numeric"),
        "show_component_total": _setting(settings, "show_component_total"),
        "show_component_symbolic": _setting(settings, "show_component_symbolic"),
        "show_component_operation": _setting(settings, "show_component_operation"),
        # Copied from results.component — the adapter never computes these.
        "total_latex": component["total_latex"],
        "total_decimal_string": format_decimal(component["total_value"], decimal_places),
        "operation_latex": component["operation_latex"],
        "operation_decimal_string": format_operation_decimal_string(
            [member["results"]["numeric_value"] for member in members], decimal_places
        ),
        "components": components,
    }


def _output_group_item(extended_json, display_defaults, members, label) -> dict:
    outputs = []
    for member in members:  # already ordered by id_output (ids)
        settings = resolve_display(display_defaults, extended_json, member)
        results = member["results"]
        quantity_label = resolve_quantity_label(member)
        show_numeric, decimal_string = _resolve_numeric(
            settings, results["numeric_value"], _setting(settings, "decimal_places")
        )
        outputs.append(
            {
                "id_output": member["id_output"],
                "output_label": output_label(member["id_output"]),
                "quantity_label": quantity_label,
                "units": derive_units(quantity_label, settings),
                "show_quantity": _setting(settings, "show_quantity"),
                "show_symbolic": _setting(settings, "show_symbolic"),
                "show_numeric": show_numeric,
                "problem_latex": results["problem_latex"],
                "solution_latex": results["solution_latex"],
                "decimal_string": decimal_string,
            }
        )
    return {"kind": "output_group", "exercise_label": label, "outputs": outputs}
