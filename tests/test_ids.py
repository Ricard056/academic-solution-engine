"""Tests for ID/grouping/sorting helpers (bible/65_id_system_v3_2.md).

Pure-structure checks: sorting order (id, id_letter, sequence), grouping by
(id, id_letter), mode detection, defensive ordering for invalid ids, and
no-mutation guarantees. Aggregation itself is NOT tested here (M4B).
"""

import copy

from solucionario.ids import (
    MODE_COMPONENT,
    MODE_OUTPUT,
    MODE_STANDARD,
    group_exercises,
    group_key,
    group_mode,
    member_sequence,
    sort_exercises,
    sort_key,
)
from solucionario.validation import validate_group


def make(id, letter=None, component=None, output=None, tag=None) -> dict:
    """Minimal exercise for structure tests; `tag` marks identity in asserts."""
    exercise = {"id": id, "type": "integral", "function": "1", "integrals": []}
    if letter is not None:
        exercise["id_letter"] = letter
    if component is not None:
        exercise["id_component"] = component
    if output is not None:
        exercise["id_output"] = output
    if tag is not None:
        exercise["tag"] = tag
    return exercise


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def test_sorts_numeric_ids():
    result = sort_exercises([make(3), make(1), make(2)])
    assert [e["id"] for e in result] == [1, 2, 3]


def test_float_id_sorts_by_value():
    result = sort_exercises([make(2), make(1.5), make(1)])
    assert [e["id"] for e in result] == [1, 1.5, 2]


def test_id_letter_ordering_unlettered_first_then_alphabetic():
    result = sort_exercises([make(1, "b"), make(1, "a"), make(1)])
    assert [e.get("id_letter") for e in result] == [None, "a", "b"]


def test_component_ordering_by_id_component():
    result = sort_exercises([make(5, component=2), make(5, component=1)])
    assert [e["id_component"] for e in result] == [1, 2]


def test_output_ordering_by_id_output():
    result = sort_exercises([make(6, output=3), make(6, output=1), make(6, output=2)])
    assert [e["id_output"] for e in result] == [1, 2, 3]


def test_stable_ordering_with_mixed_ids_letters_and_sequences():
    shuffled = [
        make(2, "a", tag="2a"),
        make(1, "b", tag="1b"),
        make(3, tag="3"),
        make(1, "a", component=2, tag="1a-c2"),
        make(1, "a", component=1, tag="1a-c1"),
    ]
    result = sort_exercises(shuffled)
    assert [e["tag"] for e in result] == ["1a-c1", "1a-c2", "1b", "2a", "3"]


def test_sort_is_stable_for_equal_keys():
    first, second = make(1, "a", tag="first"), make(1, "a", tag="second")
    result = sort_exercises([first, second])
    assert [e["tag"] for e in result] == ["first", "second"]


def test_sort_and_group_keys_ignore_solver_type():
    """bible 65/92 (D1): solver identity never participates in any sorting
    or grouping key — for recognized, unknown, non-string, and unhashable
    authored type tokens alike."""
    base = make(1, "a")
    for token in ("gradient", "bogus", None, 7, [], {}):
        variant = dict(base)
        variant["type"] = token
        assert group_key(variant) == group_key(base)
        assert sort_key(variant) == sort_key(base)
    absent = dict(base)
    del absent["type"]
    assert group_key(absent) == group_key(base)
    assert sort_key(absent) == sort_key(base)


def test_equal_key_members_of_different_types_keep_authored_order():
    """bible 65 ordering guarantees: stable authored relative order for
    identical complete structural keys is type-blind — sorting never
    partitions or reorders by solver identity."""
    integral = make(1, "a", tag="first")
    gradient = dict(make(1, "a", tag="second"), type="gradient")
    assert [e["tag"] for e in sort_exercises([integral, gradient])] == [
        "first", "second",
    ]
    assert [e["tag"] for e in sort_exercises([gradient, integral])] == [
        "second", "first",
    ]


def test_non_numeric_id_sorts_after_numeric_without_raising():
    result = sort_exercises([make("10"), make(2), make(1)])
    assert [e["id"] for e in result] == [1, 2, "10"]


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def test_group_key_uses_empty_string_for_absent_letter():
    assert group_key(make(1)) == (1, "")
    assert group_key(make(1, "a")) == (1, "a")


def test_groups_by_id_and_letter():
    exercises = [
        make(1, "b", tag="1b"),
        make(2, tag="2"),
        make(1, "a", component=2, tag="1a-c2"),
        make(1, "a", component=1, tag="1a-c1"),
    ]
    groups = group_exercises(exercises)
    assert [key for key, _ in groups] == [(1, "a"), (1, "b"), (2, "")]
    members_by_key = {key: [m["tag"] for m in members] for key, members in groups}
    assert members_by_key[(1, "a")] == ["1a-c1", "1a-c2"]  # ordered by sequence
    assert members_by_key[(1, "b")] == ["1b"]
    assert members_by_key[(2, "")] == ["2"]


def test_grouping_is_input_order_independent():
    a = [make(2), make(1, "a", component=1), make(1, "a", component=2)]
    b = [make(1, "a", component=2), make(2), make(1, "a", component=1)]
    keys_a = [key for key, _ in group_exercises(a)]
    keys_b = [key for key, _ in group_exercises(b)]
    assert keys_a == keys_b == [(1, "a"), (2, "")]


def test_grouping_with_non_numeric_id_does_not_raise():
    # The user-approved constraint: defensive group ordering, numeric first.
    groups = group_exercises([make("10"), make(2), make(1)])
    assert [key for key, _ in groups] == [(1, ""), (2, ""), ("10", "")]


# ---------------------------------------------------------------------------
# Mode detection and sequences
# ---------------------------------------------------------------------------

def test_mode_standard():
    assert group_mode([make(1)]) == MODE_STANDARD


def test_mode_component():
    members = [make(5, component=1), make(5, component=2)]
    assert group_mode(members) == MODE_COMPONENT


def test_mode_output():
    members = [make(6, output=1), make(6, output=2)]
    assert group_mode(members) == MODE_OUTPUT


def test_mode_mixed_is_none():
    assert group_mode([make(1), make(1, component=1)]) is None
    assert group_mode([make(1), make(1, output=1)]) is None
    assert group_mode([make(1, component=1), make(1, output=1)]) is None


def test_mode_both_fields_on_one_member_is_none():
    assert group_mode([make(1, component=1, output=1)]) is None


def test_mode_empty_group_is_none():
    assert group_mode([]) is None


def test_member_sequence():
    assert member_sequence(make(1, component=3)) == 3
    assert member_sequence(make(1, output=2)) == 2
    assert member_sequence(make(1)) is None


# ---------------------------------------------------------------------------
# Composition with validate_group (no duplicated validation logic)
# ---------------------------------------------------------------------------

def test_groups_feed_validate_group():
    exercises = [
        make(5, component=1),
        make(5, component=3),  # gap: 1, 3
        make(6, output=1),
        make(6, output=2),  # valid
    ]
    results = {key: validate_group(members) for key, members in group_exercises(exercises)}
    assert "sequence gap" in results[(5, "")]
    assert results[(6, "")] is None


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------

def test_helpers_do_not_mutate_input():
    exercises = [
        make(2, "b", tag="x"),
        make(1, component=2),
        make(1, component=1),
        make("10"),
    ]
    snapshot = copy.deepcopy(exercises)

    sorted_result = sort_exercises(exercises)
    group_exercises(exercises)

    assert exercises == snapshot  # list order and dict contents untouched
    assert sorted_result is not exercises  # new list, not an in-place sort
    assert sorted_result[0] is exercises[2]  # same dict references, no copies
