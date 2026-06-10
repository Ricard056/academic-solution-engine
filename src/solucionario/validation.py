"""Three-tier input validation (document / exercise / group).

Implements the validation matrix of bible/90_phase1_scope_v3_2.md with the
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

# Phase 1 has exactly one solver type (bible 90). Anything else is unknown —
# including the deferred "gradient"/"derivative" types of bible 09.
KNOWN_TYPES = frozenset({"integral"})

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

    if problems:
        raise DocumentValidationError("; ".join(problems))


# ---------------------------------------------------------------------------
# Exercise tier
# ---------------------------------------------------------------------------

def validate_exercise(exercise: dict) -> str | None:
    """Return a diagnostic message if this one exercise must render as ERROR.

    Assumes the document tier passed (id is present). Returns None if valid.
    The remaining exercise-tier trigger of the matrix — "cleaner or solver
    cannot process an expression" — is runtime behavior reported by those
    stages, not re-checked here.
    """
    if "id" in exercise and not _is_number(exercise["id"]):
        return f"id must be a number, got {exercise['id']!r}"

    if not _has(exercise, "type"):
        return "type is missing"
    if exercise["type"] not in KNOWN_TYPES:
        return f"unknown type: {exercise['type']!r}"

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
