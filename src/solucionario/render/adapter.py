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
)
from solucionario.render.labels import (
    derive_units,
    exercise_label,
    output_label,
    resolve_quantity_label,
)
from solucionario.validation import validate_group

ERROR_MESSAGE = "ERROR: no se pudo procesar este ejercicio."

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
}


def build_render_model(extended_json: dict, display_defaults: dict) -> dict:
    """Canonical Extended JSON + hardcoded defaults -> closed render model."""
    items: list[dict] = []
    for _key, members in group_exercises(extended_json.get("exercises") or []):
        items.extend(_group_items(extended_json, display_defaults, members))
    return {
        "document": _document(extended_json.get("metadata") or {}),
        "items": items,
    }


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
        return [
            _error_item(exercise_label(member))
            if _failed(member)
            else _standard_item(extended_json, display_defaults, member)
            for member in members
        ]
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
