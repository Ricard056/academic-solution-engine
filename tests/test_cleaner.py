"""Tests for the expression cleaner.

Covers the golden cases in bible/60_expression_cleaner_v3_2.md: every row of
the "Golden Test Cases" table, the rejected transformations, and the Ex 8
integrand from bible/46_test_data_integral_edge_cases_v3_2.json.
"""

import pytest

from solucionario.cleaner import CleanerError, _validate_parseable, clean_expression

# Every accepted row of the bible 60 golden table, in table order.
GOLDEN_TABLE = [
    ("x^2 + y^2", "x**2 + y**2"),
    ("sin^-1(x/2)", "asin(x/2)"),
    ("sin^2(x) + cos^2(x)", "sin(x)**2 + cos(x)**2"),
    ("ln(x) + log10(y)", "log(x) + log10(y)"),
    ("log7(x^2)", "log(x**2, 7)"),
    ("inf", "float('inf')"),
    ("  x +  y  ", "x + y"),
    ("tan^3(theta)", "tan(theta)**3"),
    ("arccos(0.5)", "acos(0.5)"),
    ("2*sin(x)", "2*sin(x)"),
]

EXTRA_ACCEPTED = [
    ("ln(x)", "log(x)"),
    ("cos^2(x)", "cos(x)**2"),
    ("cos^-1(x)", "acos(x)"),
    ("tan^-1(y)", "atan(y)"),
    ("arcsin(x)", "asin(x)"),
    ("arctan(x)", "atan(x)"),
    ("-inf", "float('-inf')"),
    ("log2(x)", "log2(x)"),
    ("x    +    y", "x + y"),
    ("(x+1)^3", "(x+1)**3"),
    ("sin^2(cos^2(x))", "sin(cos(x)**2)**2"),
    ("exp(1)", "exp(1)"),
    ("pi/2", "pi/2"),
    # Ex 8 of bible/46: ln + trig power in one integrand.
    ("ln(x) + sin^2(y)", "log(x) + sin(y)**2"),
]


@pytest.mark.parametrize("raw, expected", GOLDEN_TABLE)
def test_golden_table(raw, expected):
    assert clean_expression(raw) == expected


@pytest.mark.parametrize("raw, expected", EXTRA_ACCEPTED)
def test_extra_accepted(raw, expected):
    assert clean_expression(raw) == expected


# Rejected transformations (bible 60): never guessed, must become errors.
@pytest.mark.parametrize(
    "raw",
    [
        "2x",  # implicit multiplication (golden table ERROR row; 46 Ex 9)
        "√(x+y)",  # radical symbol
        "|x|",  # absolute-value pipes
        "sin^2(x",  # unbalanced parentheses
    ],
)
def test_rejected_expressions_raise(raw):
    with pytest.raises(CleanerError, match="Cannot parse expression"):
        clean_expression(raw)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("inf", "float('inf')"),
        ("-inf", "float('-inf')"),
    ],
)
def test_infinity_outputs_pass_parse_check(raw, expected):
    # clean_expression ends with the parse check, so returning at all proves
    # the cleaned string parsed; assert the exact bible 60 output too.
    cleaned = clean_expression(raw)
    assert cleaned == expected
    # And prove it directly: the cleaned string parses on its own.
    _validate_parseable(cleaned, raw)


def test_error_message_carries_original_expression():
    with pytest.raises(CleanerError, match=r"Cannot parse expression: 2x"):
        clean_expression("2x")
