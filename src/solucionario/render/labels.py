"""Render-only labels and quantity/unit resolution (bible 85/70/65).

Pure, adapter-facing but adapter-independent helpers. They read plain dicts
and return plain strings: no formatting, no render items, no mutation, no
imports. exercise_label/output_label are render-only strings (bible 65) —
they never exist in input or Extended JSON.

The render-model units value is a plain token ("u", "u^2", "kg"); the
TEMPLATE wraps it in \\mathrm{...} (bible 85, P4) — nothing here wraps.

Document-level labels (assignment type map, course map, title/subtitle)
belong to the render adapter milestone, not this module.
"""


def _format_number(value) -> str:
    """Render a numeric id without a spurious ".0" (1 -> "1", 1.0 -> "1");
    anything non-numeric stringifies defensively (error items still need a
    deterministic label)."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def exercise_label(exercise: dict) -> str:
    """bible 85: id=1 -> "1"; id=1, id_letter="a" -> "1.a"."""
    label = _format_number(exercise.get("id"))
    letter = exercise.get("id_letter")
    if letter is not None and str(letter) != "":
        return f"{label}.{letter}"
    return label


def output_label(id_output) -> str:
    """bible 85: id_output=1 -> "Resultado 1" (es-MX hardcoded, Phase 1)."""
    return f"Resultado {_format_number(id_output)}"


def resolve_quantity_label(exercise: dict) -> str:
    """Quantity label resolution, bible 85 order:

    1. display_override.quantity_label
    2. explicit exercise quantity
    3. inferred (bible 70/90): 2 integrals + function "1" -> "A";
       3 integrals + function "1" -> "V"; anything else -> "R".

    coordinate_system is never consulted (computationally passive): a
    Jacobian written into function makes it != "1", so transformed
    area/volume integrals need explicit quantity (bible 80/90).
    """
    override = exercise.get("display_override")
    if isinstance(override, dict) and override.get("quantity_label") is not None:
        label = override["quantity_label"]
        return label if isinstance(label, str) else str(label)

    quantity = exercise.get("quantity")
    if quantity is not None:
        return quantity if isinstance(quantity, str) else str(quantity)

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


def derive_units(quantity_label: str, resolved_display: dict) -> str:
    """Unit derivation, bible 85 order (first match wins):

    1. units_override from the resolved display config -> verbatim. (It can
       only have survived resolution from display_override — bible 90.)
    2. by resolved quantity label: "A" -> default_units + "^2",
       "V" -> default_units + "^3", anything else -> default_units bare.
    3. default_units falls back to "u" when missing or empty.
    """
    override = resolved_display.get("units_override")
    if override is not None:
        return override

    base = resolved_display.get("default_units")
    if not isinstance(base, str) or base == "":
        base = "u"

    if quantity_label == "A":
        return f"{base}^2"
    if quantity_label == "V":
        return f"{base}^3"
    return base
