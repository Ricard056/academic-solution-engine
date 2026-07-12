"""Tests for display-settings merge resolution (bible 70/85).

Covers the resolution example in bible/70_display_system_v3_2.md, level
precedence, override-only field handling (bible 90), file_naming_mode
exclusion (70 P10), group-level resolution (85), safe defaults, purity, and
the real config/display_defaults/default.json as a fixture.
"""

import copy
import json
from pathlib import Path

from solucionario.display import resolve_display, resolve_group_display

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "display_defaults" / "default.json"

HARDCODED = {
    "show_input": True,
    "show_symbolic": True,
    "show_numeric": True,
    "show_quantity": True,
    "decimal_places": 4,
    "default_units": "u",
    "language": "es-MX",
}


def make_exercise(**overrides) -> dict:
    exercise = {"id": 1, "type": "integral"}
    exercise.update(overrides)
    return exercise


# ---------------------------------------------------------------------------
# Bible 70 resolution example, verbatim
# ---------------------------------------------------------------------------

def test_bible_70_resolution_example():
    hardcoded = {"show_input": True, "decimal_places": 4, "show_symbolic": True}
    document = {
        "display_default": {"show_input": False, "decimal_places": 6},
        "display_integral": {"decimal_places": 8},
    }
    exercise = make_exercise(display_override={"show_input": True})

    assert resolve_display(hardcoded, document, exercise) == {
        "show_input": True,  # display_override wins
        "decimal_places": 8,  # display_integral wins
        "show_symbolic": True,  # hardcoded template (nothing overrode it)
    }


# ---------------------------------------------------------------------------
# Level precedence
# ---------------------------------------------------------------------------

def test_hardcoded_defaults_apply_when_nothing_else_specified():
    assert resolve_display(HARDCODED, {}, make_exercise()) == HARDCODED


def test_display_default_overrides_hardcoded():
    document = {"display_default": {"show_input": False}}
    resolved = resolve_display(HARDCODED, document, make_exercise())
    assert resolved["show_input"] is False
    assert resolved["show_symbolic"] is True  # untouched key inherited


def test_display_integral_overrides_display_default():
    document = {
        "display_default": {"decimal_places": 6},
        "display_integral": {"decimal_places": 8},
    }
    assert resolve_display(HARDCODED, document, make_exercise())["decimal_places"] == 8


def test_display_override_wins_over_everything():
    document = {
        "display_default": {"decimal_places": 6, "show_symbolic": False},
        "display_integral": {"decimal_places": 8},
    }
    exercise = make_exercise(display_override={"decimal_places": 2, "show_symbolic": True})
    resolved = resolve_display(HARDCODED, document, exercise)
    assert resolved["decimal_places"] == 2  # the Ex-7-style B1 guard, config level
    assert resolved["show_symbolic"] is True


def test_solver_key_is_derived_from_exercise_type():
    document = {"display_integral": {"show_input": False}}
    # type "integral" picks up display_integral...
    assert resolve_display(HARDCODED, document, make_exercise())["show_input"] is False
    # ...a different type does not.
    other = make_exercise(type="other")
    assert resolve_display(HARDCODED, document, other)["show_input"] is True


# ---------------------------------------------------------------------------
# Override-only fields (bible 90): valid only inside display_override
# ---------------------------------------------------------------------------

def test_override_only_fields_honored_from_display_override():
    exercise = make_exercise(
        display_override={"quantity_label": "Q", "units_override": "C"}
    )
    resolved = resolve_display(HARDCODED, {}, exercise)
    assert resolved["quantity_label"] == "Q"
    assert resolved["units_override"] == "C"


def test_override_only_fields_stripped_from_lower_levels():
    document = {
        "display_default": {"quantity_label": "M"},
        "display_integral": {"units_override": "kg"},
    }
    resolved = resolve_display(HARDCODED, document, make_exercise())
    assert "quantity_label" not in resolved
    assert "units_override" not in resolved


# ---------------------------------------------------------------------------
# Non-display and internal keys never merge (70 P10)
# ---------------------------------------------------------------------------

def test_file_naming_mode_never_enters_resolved_config():
    hardcoded = {**HARDCODED, "file_naming_mode": "production"}
    document = {"display_default": {"file_naming_mode": "testing"}}
    exercise = make_exercise(display_override={"file_naming_mode": "testing"})
    resolved = resolve_display(hardcoded, document, exercise)
    assert "file_naming_mode" not in resolved


def test_underscore_keys_never_enter_resolved_config():
    hardcoded = {**HARDCODED, "_comment": "x", "_version": "3.2"}
    document = {"display_default": {"_note": "y", "show_input": False}}
    resolved = resolve_display(hardcoded, document, make_exercise())
    assert all(not key.startswith("_") for key in resolved)
    assert resolved["show_input"] is False


# ---------------------------------------------------------------------------
# Group-level resolution (bible 85; user constraint 2)
# ---------------------------------------------------------------------------

def test_group_display_merges_three_levels_only():
    document = {
        "display_default": {"decimal_places": 6, "show_component_total": False},
        "display_integral": {"decimal_places": 8},
    }
    resolved = resolve_group_display(HARDCODED, document)
    assert resolved["decimal_places"] == 8
    assert resolved["show_component_total"] is False
    assert resolved["show_input"] is True  # hardcoded inherited


def test_group_display_never_reads_display_override():
    # resolve_group_display takes no exercise at all — its signature cannot
    # see a display_override. Assert the resolved group config matches the
    # document-level merge even when members would override.
    document = {"display_default": {"decimal_places": 6}}
    group_resolved = resolve_group_display(HARDCODED, document)
    assert group_resolved["decimal_places"] == 6  # member override (2) invisible

    member = make_exercise(display_override={"decimal_places": 2})
    member_resolved = resolve_display(HARDCODED, document, member)
    assert member_resolved["decimal_places"] == 2  # but per-member chain sees it


def test_group_display_strips_override_only_fields():
    document = {"display_default": {"quantity_label": "M", "show_input": False}}
    resolved = resolve_group_display(HARDCODED, document)
    assert "quantity_label" not in resolved
    assert resolved["show_input"] is False


# ---------------------------------------------------------------------------
# Safe defaults and purity
# ---------------------------------------------------------------------------

def test_missing_display_blocks_use_safe_defaults():
    assert resolve_display(HARDCODED, {}, {"id": 1, "type": "integral"}) == HARDCODED
    assert resolve_group_display(HARDCODED, {}) == HARDCODED


def test_junk_display_blocks_are_ignored():
    document = {"display_default": "nope", "display_integral": 42}
    exercise = make_exercise(display_override=["not", "a", "dict"])
    assert resolve_display(HARDCODED, document, exercise) == HARDCODED


def test_inputs_are_not_mutated_and_result_is_new():
    hardcoded = {**HARDCODED, "_comment": "x"}
    document = {"display_default": {"decimal_places": 6}}
    exercise = make_exercise(display_override={"show_input": False})
    snapshots = copy.deepcopy((hardcoded, document, exercise))

    resolved = resolve_display(hardcoded, document, exercise)
    resolved["decimal_places"] = 99  # mutating the result...

    assert (hardcoded, document, exercise) == snapshots  # ...touches nothing
    assert document["display_default"]["decimal_places"] == 6


# ---------------------------------------------------------------------------
# Real hardcoded template fixture (config/display_defaults/default.json)
# ---------------------------------------------------------------------------

def test_real_default_config_resolves_to_bible_50_values():
    hardcoded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    resolved = resolve_display(hardcoded, {}, make_exercise())
    assert resolved == {
        "show_input": True,
        "show_symbolic": True,
        "show_numeric": True,
        "show_quantity": True,
        "decimal_places": 4,
        "default_units": "u",
        "language": "es-MX",
        "show_component_quantity": True,
        "show_component_symbolic": True,
        "show_component_operation": True,
        "show_component_total": True,
        # Phase 2A gradient flags (bible 50/70) — global hardcoded template,
        # merged into every exercise's resolved config like any other field.
        "show_gradient": True,
        "show_gradient_evaluated": True,
        "show_magnitude": True,
        "show_unit_vector": True,
        "show_directional_derivative": True,
        "show_theta_max": True,
    }
    # _comment/_version/file_naming_mode from the file never merge.
    assert "file_naming_mode" not in resolved
