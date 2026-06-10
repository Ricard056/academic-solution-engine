"""Display-settings merge hierarchy (bible/70_display_system_v3_2.md).

Pure resolution helpers for the three-level display hierarchy on top of the
hardcoded template (bible 50 / config/display_defaults/default.json):

    hardcoded -> display_default -> display_{type} -> display_override

Each level is a plain dict.update: a level overrides only the keys it
specifies; all fields are optional at every level (bible 70). Sanitation at
every level: underscore keys (the config file's _comment/_version) and
file_naming_mode are dropped — file_naming_mode is a PROCESSING default
owned by metadata, never merged into display config (bible 70, P10).

quantity_label and units_override are valid ONLY inside display_override
(bible 90): they are stripped when authored at lower levels and survive
resolution only from the override level.

This module merges config; it does not format numbers (render/formatting),
derive units, resolve quantity labels, build labels, or render — those are
adapter responsibilities (bible 85). No file I/O here: the hardcoded
template arrives as a dict loaded by the caller (the adapter signature is
build_render_model(extended_json, defaults), bible 85).
"""

# Valid only inside display_override (bible 90, Phase 1 contract).
OVERRIDE_ONLY_FIELDS = frozenset({"quantity_label", "units_override"})

# Processing defaults that must never enter resolved display config (70 P10).
_NON_DISPLAY_KEYS = frozenset({"file_naming_mode"})


def _clean_level(block) -> dict:
    """One merge level: dict or absent; drops internal/non-display keys."""
    if not isinstance(block, dict):
        return {}
    return {
        key: value
        for key, value in block.items()
        if isinstance(key, str)
        and not key.startswith("_")
        and key not in _NON_DISPLAY_KEYS
    }


def resolve_group_display(hardcoded: dict, document: dict, exercise_type: str = "integral") -> dict:
    """Group-level display resolution (bible 85, component groups).

    Merges hardcoded -> display_default -> display_{exercise_type} ONLY.
    Never reads any exercise-level display_override; per-component overrides
    are not honored for group-level fields in Phase 1 (bible 85).
    """
    resolved = _clean_level(hardcoded)
    resolved.update(_clean_level(document.get("display_default")))
    if isinstance(exercise_type, str) and exercise_type:
        resolved.update(_clean_level(document.get(f"display_{exercise_type}")))
    for key in OVERRIDE_ONLY_FIELDS:
        resolved.pop(key, None)
    return resolved


def resolve_display(hardcoded: dict, document: dict, exercise: dict) -> dict:
    """Full display resolution for one exercise (bible 70 merge chain).

    Returns a new render-ready settings dict; never mutates its inputs.
    """
    resolved = resolve_group_display(hardcoded, document, exercise.get("type"))
    resolved.update(_clean_level(exercise.get("display_override")))
    return resolved
