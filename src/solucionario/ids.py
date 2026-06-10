"""Exercise identification: grouping, modes, and sorting.

Pure, structure-only helpers over exercise dicts (bible/65_id_system_v3_2.md):
they read only the ID fields (id / id_letter / id_component / id_output),
never mutate input, and never solve, aggregate, format, or render. Display
labels like "1.a" are render-only (bible 65) and belong to the render
adapter, not here.

These helpers make no validity decisions: callers run
validation.validate_group() per group to learn WHY a group is malformed.
group_mode() only answers "not classifiable" with None.

Defensive ordering: a non-numeric id is an exercise-tier ERROR (bible 90),
but the exercise still needs a deterministic position in the output, so all
ordering uses a type-rank guard — missing first, numbers by value, everything
else after numbers by its string form — instead of crashing with TypeError.
"""

MODE_STANDARD = "standard"
MODE_COMPONENT = "component"
MODE_OUTPUT = "output"


def _has(exercise: dict, key: str) -> bool:
    """Present and not JSON null."""
    return exercise.get(key) is not None


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _order_rank(value) -> tuple:
    """Crash-proof ordering key: (rank, numeric, text), always comparable."""
    if value is None:
        return (0, 0.0, "")
    if _is_number(value):
        return (1, float(value), "")
    return (2, 0.0, str(value))


def _letter(exercise: dict) -> str:
    letter = exercise.get("id_letter")
    return str(letter) if letter is not None else ""


def group_key(exercise: dict) -> tuple:
    """(id, id_letter) — the group identity. id_letter is "" when absent."""
    identifier = exercise.get("id")
    if isinstance(identifier, (dict, list)):  # unhashable junk: keep grouping alive
        identifier = repr(identifier)
    return (identifier, _letter(exercise))


def member_sequence(exercise: dict):
    """id_component or id_output, whichever is present; None for standard."""
    if _has(exercise, "id_component"):
        return exercise["id_component"]
    if _has(exercise, "id_output"):
        return exercise["id_output"]
    return None


def sort_key(exercise: dict) -> tuple:
    """Bible 65 sorting order: id, id_letter, id_component/id_output."""
    return (
        _order_rank(exercise.get("id")),
        _letter(exercise),
        _order_rank(member_sequence(exercise)),
    )


def sort_exercises(exercises: list[dict]) -> list[dict]:
    """New stably-sorted list (same dict references, no mutation)."""
    return sorted(exercises, key=sort_key)


def group_exercises(exercises: list[dict]) -> list[tuple[tuple, list[dict]]]:
    """[(group_key, members), ...] — groups ordered by (id, id_letter),
    members ordered by sequence within each group, regardless of input order.

    Group ordering uses the same defensive rank as sort_key(), so invalid
    non-numeric ids order after numeric ids instead of raising TypeError.
    """
    groups: dict[tuple, list[dict]] = {}
    for exercise in exercises:
        groups.setdefault(group_key(exercise), []).append(exercise)

    ordered_keys = sorted(groups, key=lambda key: (_order_rank(key[0]), key[1]))
    return [(key, sorted(groups[key], key=sort_key)) for key in ordered_keys]


def group_mode(members: list[dict]) -> str | None:
    """"standard" | "component" | "output" for a coherent group; None when
    the group is not classifiable (empty, mixed modes, or a member carrying
    both id_component and id_output). validate_group() reports the why."""
    if not members:
        return None
    if any(_has(m, "id_component") and _has(m, "id_output") for m in members):
        return None

    component = sum(1 for m in members if _has(m, "id_component"))
    output = sum(1 for m in members if _has(m, "id_output"))
    if component == len(members) and output == 0:
        return MODE_COMPONENT
    if output == len(members) and component == 0:
        return MODE_OUTPUT
    if component == 0 and output == 0:
        return MODE_STANDARD
    return None
