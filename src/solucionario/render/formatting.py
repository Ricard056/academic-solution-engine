"""Render-time decimal formatting (bible 85, Decimal Formatting Rule).

Decimals MUST use decimal.Decimal with ROUND_HALF_UP; never round() or
f"{v:.nf}" — both are round-half-to-even and silently violate the contract.
The recipe is bible 85 verbatim: Decimal(str(value)) — the float's shortest
repr, so artifacts like 2.675 (binary ~2.67499...) format as "2.68" —
quantized to exactly decimal_places digits, trailing zeros kept.

Render-only: pure value -> str helpers consumed by the render adapter when
building render-model fields (decimal_string, total_decimal_string,
operation_decimal_string). Nothing here writes to dicts; Extended JSON never
contains formatted decimals (schema-closure test in test_extended_json.py).
This module imports stdlib decimal only (AST-guarded by test_formatting.py).

Unit derivation (bible 85, Unit Derivation Rule) is NOT implemented yet —
it arrives with the render adapter milestone.
"""

from decimal import ROUND_HALF_UP, Decimal


def format_decimal(value, decimal_places: int) -> str:
    """Fixed-point string with exactly decimal_places digits, ROUND_HALF_UP.

    decimal_places=0 yields no decimal point ("3"). Raises ValueError for an
    invalid decimal_places (negative, bool, or non-int) and for non-finite
    values (NaN, Infinity, -Infinity) — they must never format silently.
    """
    if (
        isinstance(decimal_places, bool)
        or not isinstance(decimal_places, int)
        or decimal_places < 0
    ):
        raise ValueError(
            f"decimal_places must be a non-negative int, got {decimal_places!r}"
        )

    decimal_value = Decimal(str(value))
    if not decimal_value.is_finite():
        raise ValueError(f"cannot format non-finite value: {value!r}")

    quantum = Decimal(1).scaleb(-decimal_places)
    return str(decimal_value.quantize(quantum, rounding=ROUND_HALF_UP))


def format_operation_decimal_string(values, decimal_places: int) -> str:
    """Formatted parts joined with " + " — the Phase 1 sum join used for the
    Total line's operation_decimal_string (bible 85)."""
    return " + ".join(format_decimal(value, decimal_places) for value in values)


def format_vector_decimal(values, decimal_places: int) -> str:
    """Complete decimal vector in the canonical delimiter (bible 85, Phase 2A):

        format_vector_decimal([8.0, 4.0], 4)
        -> "\\left\\langle 8.0000, \\; 4.0000 \\right\\rangle"

    The vector analogue of format_operation_decimal_string: each component
    formatted independently by format_decimal (Decimal + ROUND_HALF_UP,
    trailing zeros kept), order and count preserved, input list untouched.
    Validation (invalid decimal_places, non-finite components) propagates
    from format_decimal."""
    components = [format_decimal(value, decimal_places) for value in values]
    return r"\left\langle " + r", \; ".join(components) + r" \right\rangle"
