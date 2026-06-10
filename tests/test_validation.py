"""Tests for three-tier validation (document / exercise / group).

Covers the validation matrix in bible/90_phase1_scope_v3_2.md: document-level
hard stops, exercise-level ERROR triggers, and group-level ERROR triggers.
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


@pytest.mark.parametrize("bad_type", ["derivative", "gradient", "Integral", 7])
def test_unknown_type_is_exercise_error(bad_type):
    # "derivative"/"gradient" are deferred solvers (bible 09) — unknown in Phase 1.
    assert "unknown type" in validate_exercise(make_exercise(type=bad_type))


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
