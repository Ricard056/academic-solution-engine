"""Three-tier input validation (document / exercise / group).

Implements the validation matrix of bible/90_phase1_scope_v3_2.md and the
Phase 2A gradient matrix of bible/91_phase2a_gradient_scope_v3_2.md with the
required-field rules of bible/80_json_input_spec_v3_2.md:

- Document tier — validate_document() RAISES DocumentValidationError. The
  caller must abort the whole run and write no output (bible 55).
- Exercise tier — validate_exercise() returns a diagnostic message or None.
  The caller marks that one exercise as ERROR and continues.
- Group tier — validate_group() returns a diagnostic message or None for the
  members of one (id, id_letter) group.

validate_group() is a pure, stage-agnostic helper: it checks static
group-structure problems visible from the input exercises alone. It does not
depend on solver output, Extended JSON, the render model, or pipeline state;
callers decide how a reported problem surfaces (skipping aggregation,
rendering one kind:"error" item, ...). The runtime rule "any member failed at
exercise level -> whole group errors" depends on clean/solve results and
intentionally lives outside this module.

Messages returned here are internal English diagnostics (they feed
results.error_message in Extended JSON, bible 75); the PDF-facing text is the
generic Spanish ERROR marker owned by the render adapter (bible 85).
"""

# Phase 1 integrals (bible 90) + Phase 2A gradient (bible 91). Anything else
# is unknown — including the deferred "derivative" type of bible 09.
KNOWN_TYPES = frozenset({"integral", "gradient"})

_BOUND_KEYS = ("var", "lower", "upper")


class DocumentValidationError(ValueError):
    """Hard stop: abort before solving, produce no output (bible 90/55)."""


def _is_number(value) -> bool:
    # JSON true/false arrive as Python bools, which subclass int; a boolean
    # id would "sort" but is not a NUMBER per bible 65/80.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _has(container: dict, key: str) -> bool:
    """Present and not JSON null."""
    return container.get(key) is not None


# ---------------------------------------------------------------------------
# Document tier
# ---------------------------------------------------------------------------

def validate_document(data) -> None:
    """Raise DocumentValidationError if the document cannot be processed at all."""
    if not isinstance(data, dict):
        raise DocumentValidationError("input is not a JSON object")

    problems = []

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        problems.append("metadata is missing or not an object")
    else:
        if not _has(metadata, "course"):
            problems.append("metadata.course is missing")
        assignment = metadata.get("assignment")
        if not isinstance(assignment, dict):
            problems.append("metadata.assignment is missing or not an object")
        else:
            if not _has(assignment, "type"):
                problems.append("metadata.assignment.type is missing")
            if not _has(assignment, "number"):
                problems.append("metadata.assignment.number is missing")

    exercises = data.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        problems.append("exercises is absent or empty")
    else:
        for index, exercise in enumerate(exercises):
            if not isinstance(exercise, dict):
                problems.append(f"exercise at index {index} is not an object")
            elif not _has(exercise, "id"):
                problems.append(f"exercise at index {index} is missing id")

        # Phase 2A (bible 91): single-solver documents only — mixing
        # type:"gradient" with any other PRESENT type is a hard stop (the
        # template router is undefined for mixed documents). A missing type
        # is not "another type": it stays an exercise-level ERROR.
        # Equality scans only — authored type values may be unhashable
        # (e.g. [] or {}), so no set/hash operation is safe here.
        present_types = [
            exercise.get("type")
            for exercise in exercises
            if isinstance(exercise, dict) and exercise.get("type") is not None
        ]
        has_gradient = any(value == "gradient" for value in present_types)
        has_other_type = any(value != "gradient" for value in present_types)
        if has_gradient and has_other_type:
            problems.append(
                "document mixes gradient with other exercise types "
                "(single-solver documents only in Phase 2A)"
            )

    if problems:
        raise DocumentValidationError("; ".join(problems))


# ---------------------------------------------------------------------------
# Exercise tier
# ---------------------------------------------------------------------------

def validate_exercise(exercise: dict) -> str | None:
    """Return a diagnostic message if this one exercise must render as ERROR.

    Assumes the document tier passed (id is present). Returns None if valid.
    The remaining exercise-tier triggers of the matrices — "cleaner or solver
    cannot process an expression" (90/91), a direction that only PARSES to
    zero (91), and a domain error at the point (91) — are runtime behavior
    reported by those stages, not re-checked here.
    """
    if "id" in exercise and not _is_number(exercise["id"]):
        return f"id must be a number, got {exercise['id']!r}"

    if not _has(exercise, "type"):
        return "type is missing"
    exercise_type = exercise["type"]
    # String gate BEFORE the frozenset membership test: authored type values
    # may be unhashable (e.g. [] or {}) and must error, never raise.
    if not isinstance(exercise_type, str):
        return f"type must be a string, got {exercise_type!r}"
    if exercise_type not in KNOWN_TYPES:
        return f"unknown type: {exercise_type!r}"

    if exercise_type == "gradient":
        return _validate_gradient_fields(exercise)
    return _validate_integral_fields(exercise)


def _validate_integral_fields(exercise: dict) -> str | None:
    """Integral solver fields (bible 80/90) — the Phase 1 checks, unchanged."""
    if not _has(exercise, "function"):
        return "function is missing"
    if not isinstance(exercise["function"], str):
        return f"function must be a string, got {exercise['function']!r}"

    if not _has(exercise, "integrals"):
        return "integrals is missing"
    integrals = exercise["integrals"]
    if not isinstance(integrals, list):
        return "integrals must be an array"
    for index, bound in enumerate(integrals):
        if not isinstance(bound, dict):
            return f"integral bound {index + 1} is not an object"
        missing = [key for key in _BOUND_KEYS if not _has(bound, key)]
        if missing:
            return f"integral bound {index + 1} is missing {', '.join(missing)}"

    return None


# Coordinate containers of the gradient contract (bible 80/91).
_GRADIENT_ARRAY_FIELDS = ("point", "initial_point", "final_point", "vector")


def _validate_gradient_fields(exercise: dict) -> str | None:
    """Gradient solver static matrix (bible 91/80, Phase 2A).

    Structural checks only. Runtime triggers — a coordinate/angle that cannot
    be cleaned or parsed, a direction that only PARSES to ⟨0, 0⟩ (including
    max_ascent with a zero gradient), and domain errors at the point — are
    reported by the cleaner/solver stages, mirroring the Phase 1 split.
    """
    if not _has(exercise, "function"):
        return "function is missing"
    if not isinstance(exercise["function"], str):
        return f"function must be a string, got {exercise['function']!r}"

    # Coordinates are 2-element arrays of strings (bible 80: raw JSON numbers
    # are rejected; Phase 2A is 2-variable).
    for field in _GRADIENT_ARRAY_FIELDS:
        if not _has(exercise, field):
            continue
        value = exercise[field]
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(entry, str) for entry in value)
        ):
            return f"{field} must be a 2-element array of strings, got {value!r}"

    if _has(exercise, "angle") and not isinstance(exercise["angle"], str):
        return f"angle must be a string, got {exercise['angle']!r}"

    if (
        _has(exercise, "direction_source")
        and exercise["direction_source"] != "max_ascent"
    ):
        return (
            "unknown direction_source: "
            f"{exercise['direction_source']!r} (Phase 2A allows only \"max_ascent\")"
        )

    # Evaluation point: exactly one of `point` or a COMPLETE two-points pair.
    has_point = _has(exercise, "point")
    has_initial = _has(exercise, "initial_point")
    has_final = _has(exercise, "final_point")
    if has_point and (has_initial or has_final):
        return "point conflicts with initial_point/final_point"
    if has_initial != has_final:
        return "incomplete two-points pair (initial_point and final_point required together)"
    if not has_point and not has_initial:
        return "no evaluation point (need point, or initial_point + final_point)"

    # At most one direction source; a complete two-points pair counts as one.
    sources = [
        name
        for name, present in (
            ("initial_point+final_point", has_initial and has_final),
            ("vector", _has(exercise, "vector")),
            ("angle", _has(exercise, "angle")),
            ('direction_source "max_ascent"', _has(exercise, "direction_source")),
        )
        if present
    ]
    if len(sources) > 1:
        return "more than one direction source: " + ", ".join(sources)

    return None


# ---------------------------------------------------------------------------
# Group tier
# ---------------------------------------------------------------------------

def validate_group(members: list[dict]) -> str | None:
    """Return a diagnostic message if this (id, id_letter) group is malformed.

    `members` are all input exercises sharing one (id, id_letter). Returns
    None if the group structure is valid. Pure and stage-agnostic — see the
    module docstring.
    """
    for member in members:
        # Phase 2A (bible 91/65): gradient is standard-items-only; either
        # grouping field on a gradient member errors the whole group.
        if member.get("type") == "gradient" and (
            _has(member, "id_component") or _has(member, "id_output")
        ):
            return (
                "a gradient exercise carries id_component or id_output "
                "(gradient is standard-items-only in Phase 2A)"
            )
        if _has(member, "id_component") and _has(member, "id_output"):
            return "an exercise carries both id_component and id_output"

    component_members = [m for m in members if _has(m, "id_component")]
    output_members = [m for m in members if _has(m, "id_output")]
    standard_count = len(members) - len(component_members) - len(output_members)

    modes_present = sum(
        1 for present in (component_members, output_members, standard_count) if present
    )
    if modes_present > 1:
        return "group mixes standard/component/output modes"

    if component_members:
        problem = _check_sequence(
            [m["id_component"] for m in component_members], "id_component"
        )
        if problem:
            return problem
        for member in component_members:
            if "component_operation" in member and member["component_operation"] != "sum":
                return (
                    "unsupported component_operation: "
                    f"{member['component_operation']!r} (Phase 1 allows only \"sum\")"
                )
        labels = {_resolved_quantity_label(m) for m in component_members}
        if len(labels) > 1:
            return (
                "component group members resolve to different quantity_labels: "
                + ", ".join(sorted(labels))
            )

    if output_members:
        problem = _check_sequence([m["id_output"] for m in output_members], "id_output")
        if problem:
            return problem

    return None


def _check_sequence(values: list, field: str) -> str | None:
    """Values must be numbers forming exactly 1..n (no gaps, no duplicates)."""
    for value in values:
        if not _is_number(value):
            return f"{field} must be a number, got {value!r}"
    if len(set(values)) != len(values):
        return f"duplicate {field} values"
    if sorted(values) != list(range(1, len(values) + 1)):
        return f"{field} sequence gap (must be sequential 1..n)"
    return None


def _resolved_quantity_label(exercise: dict) -> str:
    """Resolve a member's quantity label for the uniformity check.

    Resolution order per bible 85: display_override.quantity_label, else
    explicit quantity, else the bible 70/90 inference (2/3 integrals with
    function "1" -> A/V, anything else -> R). Whitespace normalization is the
    only cleaner transformation that can affect the literal "1", so a
    normalized comparison matches the cleaned-function rule without invoking
    the cleaner on possibly-broken expressions.
    """
    override = exercise.get("display_override")
    if isinstance(override, dict) and _has(override, "quantity_label"):
        return override["quantity_label"]
    if _has(exercise, "quantity"):
        return exercise["quantity"]

    integrals = exercise.get("integrals")
    count = len(integrals) if isinstance(integrals, list) else 0
    function = exercise.get("function")
    normalized = " ".join(function.split()) if isinstance(function, str) else ""
    if normalized == "1":
        if count == 2:
            return "A"
        if count == 3:
            return "V"
    return "R"
