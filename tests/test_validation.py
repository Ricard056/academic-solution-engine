"""Tests for three-tier validation (document / exercise / group).

Covers the validation matrix in bible/90_phase1_scope_v3_2.md — document-level
hard stops, exercise-level ERROR triggers, and group-level ERROR triggers —
plus the Phase 2A gradient matrix of bible/91_phase2a_gradient_scope_v3_2.md
(mixed-document hard stop, gradient static checks, standard-items-only rule).
"""

import pytest

from solucionario.validation import (
    DocumentValidationError,
    validate_document,
    validate_exercise,
    validate_group,
)


def make_exercise(**overrides) -> dict:
    """A valid minimal integral exercise; overrides replace or (None) drop keys."""
    exercise = {
        "id": 1,
        "type": "integral",
        "function": "1",
        "integrals": [
            {"var": "y", "lower": "0", "upper": "1"},
            {"var": "x", "lower": "0", "upper": "1"},
        ],
    }
    for key, value in overrides.items():
        if value is None:
            exercise.pop(key, None)
        else:
            exercise[key] = value
    return exercise


def make_gradient_exercise(**overrides) -> dict:
    """A valid minimal gradient exercise (point-only mode, bible 91);
    overrides replace or (None) drop keys, like make_exercise."""
    exercise = {
        "id": 1,
        "type": "gradient",
        "function": "x**2 + y**2",
        "point": ["1", "3"],
    }
    for key, value in overrides.items():
        if value is None:
            exercise.pop(key, None)
        else:
            exercise[key] = value
    return exercise


def make_document(**overrides) -> dict:
    document = {
        "metadata": {
            "course": "Calculus 3",
            "assignment": {"type": "hw", "number": 1},
        },
        "exercises": [make_exercise()],
    }
    document.update(overrides)
    return document


# ---------------------------------------------------------------------------
# Document tier (hard stop)
# ---------------------------------------------------------------------------

def test_valid_minimal_document_passes():
    validate_document(make_document())  # must not raise


@pytest.mark.parametrize("data", [None, [], "not a dict", 42])
def test_non_object_input_is_hard_stop(data):
    with pytest.raises(DocumentValidationError):
        validate_document(data)


def test_missing_metadata_is_hard_stop():
    document = make_document()
    del document["metadata"]
    with pytest.raises(DocumentValidationError):
        validate_document(document)


def test_missing_course_is_hard_stop():
    document = make_document()
    del document["metadata"]["course"]
    with pytest.raises(DocumentValidationError, match="course"):
        validate_document(document)


def test_missing_assignment_type_is_hard_stop():
    document = make_document()
    del document["metadata"]["assignment"]["type"]
    with pytest.raises(DocumentValidationError, match="assignment.type"):
        validate_document(document)


def test_missing_assignment_number_is_hard_stop():
    document = make_document()
    del document["metadata"]["assignment"]["number"]
    with pytest.raises(DocumentValidationError, match="assignment.number"):
        validate_document(document)


@pytest.mark.parametrize("exercises", [None, [], "not a list"])
def test_absent_or_empty_exercises_is_hard_stop(exercises):
    document = make_document()
    if exercises is None:
        del document["exercises"]
    else:
        document["exercises"] = exercises
    with pytest.raises(DocumentValidationError, match="exercises"):
        validate_document(document)


def test_any_exercise_missing_id_is_hard_stop():
    document = make_document(exercises=[make_exercise(), make_exercise(id=None)])
    with pytest.raises(DocumentValidationError, match="missing id"):
        validate_document(document)


def test_non_object_exercise_entry_is_hard_stop():
    document = make_document(exercises=[make_exercise(), "not an exercise"])
    with pytest.raises(DocumentValidationError, match="not an object"):
        validate_document(document)


def test_all_gradient_document_passes():
    document = make_document(
        exercises=[make_gradient_exercise(), make_gradient_exercise(id=2)]
    )
    validate_document(document)  # must not raise


def test_mixed_gradient_and_integral_document_is_hard_stop():
    # bible 91: single-solver documents only in Phase 2A.
    document = make_document(
        exercises=[make_exercise(), make_gradient_exercise(id=2)]
    )
    with pytest.raises(DocumentValidationError, match="mixes gradient"):
        validate_document(document)


def test_mixed_gradient_and_unknown_type_document_is_hard_stop():
    # "any other exercise type" (bible 91) includes unknown type strings.
    document = make_document(
        exercises=[make_gradient_exercise(), make_exercise(id=2, type="bogus")]
    )
    with pytest.raises(DocumentValidationError, match="mixes gradient"):
        validate_document(document)


def test_gradient_with_missing_type_member_is_not_a_hard_stop():
    # A missing type is not "another type": it stays an exercise-level ERROR.
    document = make_document(
        exercises=[make_gradient_exercise(), make_exercise(id=2, type=None)]
    )
    validate_document(document)  # must not raise


@pytest.mark.parametrize("bad_type", [[], {}])
def test_mixed_gradient_and_non_string_type_is_hard_stop(bad_type):
    # An unhashable present type is still "another present type" alongside
    # gradient: the existing hard stop fires — never a raw TypeError.
    document = make_document(
        exercises=[make_gradient_exercise(), make_exercise(id=2, type=bad_type)]
    )
    with pytest.raises(DocumentValidationError, match="mixes gradient"):
        validate_document(document)


@pytest.mark.parametrize("bad_type", [[], {}])
def test_integral_document_with_non_string_type_is_not_a_hard_stop(bad_type):
    # Without gradient there is no mixing rule: an unhashable type must pass
    # document-level inspection without crashing and reach exercise-level
    # validation.
    document = make_document(
        exercises=[make_exercise(), make_exercise(id=2, type=bad_type)]
    )
    validate_document(document)  # must not raise


def test_integral_with_unknown_type_member_is_not_a_hard_stop():
    # Phase 1 behavior preserved: without gradient there is no mixing rule.
    document = make_document(
        exercises=[make_exercise(), make_exercise(id=2, type="bogus")]
    )
    validate_document(document)  # must not raise


# ---------------------------------------------------------------------------
# Exercise tier (continue; one exercise becomes ERROR)
# ---------------------------------------------------------------------------

def test_valid_exercise_returns_none():
    assert validate_exercise(make_exercise()) is None


@pytest.mark.parametrize("bad_id", ["1", "a", True])
def test_non_numeric_id_is_exercise_error(bad_id):
    assert "id must be a number" in validate_exercise(make_exercise(id=bad_id))


def test_missing_type_is_exercise_error():
    assert validate_exercise(make_exercise(type=None)) == "type is missing"


@pytest.mark.parametrize("bad_type", ["derivative", "Integral"])
def test_unknown_type_is_exercise_error(bad_type):
    # "derivative" is a deferred solver (bible 09) — unknown. "gradient" is a
    # known type since Phase 2A (bible 91).
    assert "unknown type" in validate_exercise(make_exercise(type=bad_type))


@pytest.mark.parametrize("bad_type", [7, [], {}])
def test_non_string_type_is_exercise_error(bad_type):
    # Non-string type values (including unhashable [] / {}) must come back
    # as a validation ERROR, never escape as a raw TypeError.
    message = validate_exercise(make_exercise(type=bad_type))
    assert "type must be a string" in message


def test_missing_function_is_exercise_error():
    assert validate_exercise(make_exercise(function=None)) == "function is missing"


def test_non_string_function_is_exercise_error():
    assert "function must be a string" in validate_exercise(make_exercise(function=5))


def test_missing_integrals_is_exercise_error():
    assert validate_exercise(make_exercise(integrals=None)) == "integrals is missing"


def test_non_array_integrals_is_exercise_error():
    assert validate_exercise(make_exercise(integrals="nope")) == "integrals must be an array"


@pytest.mark.parametrize("missing_key", ["var", "lower", "upper"])
def test_bound_missing_key_is_exercise_error(missing_key):
    bound = {"var": "x", "lower": "0", "upper": "1"}
    del bound[missing_key]
    message = validate_exercise(make_exercise(integrals=[bound]))
    assert "integral bound 1 is missing" in message
    assert missing_key in message


def test_non_object_bound_is_exercise_error():
    message = validate_exercise(make_exercise(integrals=["0 to 1"]))
    assert message == "integral bound 1 is not an object"


# ---------------------------------------------------------------------------
# Exercise tier — gradient static matrix (bible 91/80, Phase 2A)
# ---------------------------------------------------------------------------

def test_valid_gradient_point_only():
    assert validate_exercise(make_gradient_exercise()) is None


def test_valid_gradient_two_points():
    exercise = make_gradient_exercise(
        point=None, initial_point=["0", "2"], final_point=["5", "7"]
    )
    assert validate_exercise(exercise) is None


def test_valid_gradient_point_vector():
    assert validate_exercise(make_gradient_exercise(vector=["4", "1"])) is None


def test_valid_gradient_point_angle():
    assert validate_exercise(make_gradient_exercise(angle="pi/4")) is None


def test_valid_gradient_max_ascent():
    exercise = make_gradient_exercise(direction_source="max_ascent")
    assert validate_exercise(exercise) is None


def test_gradient_missing_function_is_exercise_error():
    message = validate_exercise(make_gradient_exercise(function=None))
    assert message == "function is missing"


def test_gradient_non_string_function_is_exercise_error():
    message = validate_exercise(make_gradient_exercise(function=5))
    assert "function must be a string" in message


def test_gradient_no_evaluation_point_is_exercise_error():
    # E1 of bible 51/52: function only — no point, no two-points pair.
    message = validate_exercise(make_gradient_exercise(point=None))
    assert "no evaluation point" in message


@pytest.mark.parametrize("extra", ["initial_point", "final_point"])
def test_point_with_pair_field_is_exercise_error(extra):
    message = validate_exercise(make_gradient_exercise(**{extra: ["0", "0"]}))
    assert "point conflicts" in message


@pytest.mark.parametrize("only", ["initial_point", "final_point"])
def test_incomplete_two_points_pair_is_exercise_error(only):
    message = validate_exercise(
        make_gradient_exercise(point=None, **{only: ["0", "2"]})
    )
    assert "incomplete two-points pair" in message


@pytest.mark.parametrize(
    "overrides",
    [
        # complete two-points pair + each other source
        {"point": None, "initial_point": ["0", "2"], "final_point": ["5", "7"],
         "vector": ["4", "1"]},
        {"point": None, "initial_point": ["0", "2"], "final_point": ["5", "7"],
         "angle": "pi/4"},
        {"point": None, "initial_point": ["0", "2"], "final_point": ["5", "7"],
         "direction_source": "max_ascent"},
        # point + two of vector/angle/max_ascent
        {"vector": ["4", "1"], "angle": "pi/4"},
        {"vector": ["4", "1"], "direction_source": "max_ascent"},
        {"angle": "pi/4", "direction_source": "max_ascent"},
    ],
)
def test_multiple_direction_sources_are_exercise_error(overrides):
    message = validate_exercise(make_gradient_exercise(**overrides))
    assert "more than one direction source" in message


@pytest.mark.parametrize(
    "overrides",
    [
        {"point": ["1", 3]},
        {"vector": [4, 1]},
        {"point": None, "initial_point": [0, "2"], "final_point": ["5", "7"]},
        {"point": None, "initial_point": ["0", "2"], "final_point": ["5", 7]},
    ],
)
def test_non_string_coordinate_entry_is_exercise_error(overrides):
    # bible 80: raw JSON numbers are rejected — coordinates are strings.
    message = validate_exercise(make_gradient_exercise(**overrides))
    assert "2-element array of strings" in message


@pytest.mark.parametrize(
    "bad_value", [["1"], ["1", "2", "3"], [], "1,3", {"x": "1", "y": "3"}]
)
def test_wrong_shape_point_is_exercise_error(bad_value):
    message = validate_exercise(make_gradient_exercise(point=bad_value))
    assert "2-element array of strings" in message


def test_wrong_length_vector_is_exercise_error():
    message = validate_exercise(make_gradient_exercise(vector=["1", "2", "3"]))
    assert "2-element array of strings" in message


def test_non_string_angle_is_exercise_error():
    message = validate_exercise(make_gradient_exercise(angle=0.785))
    assert "angle must be a string" in message


def test_unknown_direction_source_is_exercise_error():
    message = validate_exercise(make_gradient_exercise(direction_source="descent"))
    assert "unknown direction_source" in message


# ---------------------------------------------------------------------------
# Group tier (whole (id, id_letter) group becomes one ERROR)
# ---------------------------------------------------------------------------

def test_single_standard_exercise_group_is_valid():
    assert validate_group([make_exercise()]) is None


def test_valid_component_group():
    members = [
        make_exercise(id_component=1, quantity="A"),
        make_exercise(id_component=2, quantity="A"),
    ]
    assert validate_group(members) is None


def test_valid_output_group():
    members = [make_exercise(id_output=1), make_exercise(id_output=2)]
    assert validate_group(members) is None


def test_both_component_and_output_on_one_exercise():
    members = [make_exercise(id_component=1, id_output=1)]
    assert "both id_component and id_output" in validate_group(members)


@pytest.mark.parametrize(
    "members",
    [
        [make_exercise(), make_exercise(id_component=1)],  # standard + component
        [make_exercise(), make_exercise(id_output=1)],  # standard + output
        [make_exercise(id_component=1), make_exercise(id_output=1)],  # comp + output
    ],
)
def test_mixed_modes_are_group_error(members):
    assert "mixes" in validate_group(members)


@pytest.mark.parametrize("field", ["id_component", "id_output"])
def test_sequence_gap_is_group_error(field):
    members = [make_exercise(**{field: 1}), make_exercise(**{field: 3})]
    assert "sequence gap" in validate_group(members)


@pytest.mark.parametrize("field", ["id_component", "id_output"])
def test_sequence_not_starting_at_1_is_group_error(field):
    members = [make_exercise(**{field: 2}), make_exercise(**{field: 3})]
    assert "sequence gap" in validate_group(members)


@pytest.mark.parametrize("field", ["id_component", "id_output"])
def test_duplicate_ids_are_group_error(field):
    members = [make_exercise(**{field: 1}), make_exercise(**{field: 1})]
    assert f"duplicate {field}" in validate_group(members)


@pytest.mark.parametrize("field", ["id_component", "id_output"])
def test_non_numeric_group_id_is_group_error(field):
    members = [make_exercise(**{field: "1"})]
    assert f"{field} must be a number" in validate_group(members)


def test_component_operation_sum_or_absent_is_valid():
    members = [
        make_exercise(id_component=1, quantity="A", component_operation="sum"),
        make_exercise(id_component=2, quantity="A"),
    ]
    assert validate_group(members) is None


def test_component_operation_other_than_sum_is_group_error():
    members = [
        make_exercise(id_component=1, quantity="A"),
        make_exercise(id_component=2, quantity="A", component_operation="product"),
    ]
    assert "unsupported component_operation" in validate_group(members)


def test_conflicting_explicit_quantities_are_group_error():
    members = [
        make_exercise(id_component=1, quantity="A"),
        make_exercise(id_component=2, quantity="V"),
    ]
    assert "different quantity_labels" in validate_group(members)


def test_conflicting_quantity_label_override_is_group_error():
    members = [
        make_exercise(id_component=1, quantity="A"),
        make_exercise(
            id_component=2, quantity="A", display_override={"quantity_label": "M"}
        ),
    ]
    assert "different quantity_labels" in validate_group(members)


def test_inferred_quantity_matching_explicit_is_not_a_conflict():
    # Member 2 has no quantity: 2 integrals + function "1" infers "A" (bible 70),
    # matching member 1's explicit "A".
    members = [
        make_exercise(id_component=1, quantity="A"),
        make_exercise(id_component=2),
    ]
    assert validate_group(members) is None


def test_inferred_quantity_conflict_is_group_error():
    # Member 2 infers "R" (function != "1"), conflicting with explicit "A".
    members = [
        make_exercise(id_component=1, quantity="A"),
        make_exercise(id_component=2, function="x + y"),
    ]
    assert "different quantity_labels" in validate_group(members)


# ---------------------------------------------------------------------------
# Group tier — gradient is standard-items-only (bible 91/65, Phase 2A)
# ---------------------------------------------------------------------------

def test_gradient_standard_group_is_valid():
    assert validate_group([make_gradient_exercise()]) is None


@pytest.mark.parametrize("field", ["id_component", "id_output"])
def test_gradient_with_grouping_field_is_group_error(field):
    members = [make_gradient_exercise(**{field: 1})]
    assert "standard-items-only" in validate_group(members)
