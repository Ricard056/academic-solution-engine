"""Expression cleaner (safe notation transformations).

Implements the SAFE transformations of bible/60_expression_cleaner_v3_2.md:
whitespace normalization, logarithms, inverse trig, trig powers, infinity
constants, and caret exponentiation. REJECTED notations (implicit
multiplication like ``2x``, ``√``, ``|x|``) are never guessed at: characters
outside the safe math set are rejected up front, and anything else
unprocessable (e.g. ``2x``) is caught by the final SymPy parse check. Both
raise CleanerError so the pipeline can mark the exercise as ERROR. (The
parse check alone is not enough: SymPy parses ``√(x+y)`` as an undefined
function named ``√`` instead of failing.)

Global transformation order (bible 60): the ln/logN/^-1/^n rewrites run
first; the generic ``^`` -> ``**`` conversion runs last on remaining carets.

SymPy is imported for parse validation only — the cleaner does not solve
and does not format.
"""

import re

from sympy.parsing.sympy_parser import parse_expr, standard_transformations


class CleanerError(ValueError):
    """Raised when an expression cannot be processed (bible 60, Error Handling)."""


# Safe math input characters: identifiers, numbers, operators, parens.
# Anything else (√, |, unicode, etc.) is a rejected notation per bible 60.
_ALLOWED_CHARS = re.compile(r"[A-Za-z0-9_ .+\-*/^(),]*\Z")

_LN = re.compile(r"\bln\b")
_ARC_TRIG = re.compile(r"\barc(sin|cos|tan)\b")
_LOG_BASE = re.compile(r"\blog(\d+)\(")
_TRIG_INVERSE = re.compile(r"\b(sin|cos|tan)\^-1\(")
_TRIG_POWER = re.compile(r"\b(sin|cos|tan)\^(\d+)\(")
_STANDALONE_INF = re.compile(r"\binf\b")
_WHOLE_NEG_INF = re.compile(r"-\s*inf")


def clean_expression(expression: str) -> str:
    """Clean one mathematical expression string (function or bound).

    Returns the cleaned, SymPy-parseable expression. Raises CleanerError if
    the cleaned result still cannot be parsed (e.g. implicit multiplication).
    """
    cleaned = " ".join(expression.split())
    if _ALLOWED_CHARS.fullmatch(cleaned) is None:
        raise CleanerError(f"Cannot parse expression: {expression}")
    cleaned = _LN.sub("log", cleaned)
    cleaned = _ARC_TRIG.sub(r"a\1", cleaned)
    cleaned = _rewrite_log_bases(cleaned)
    cleaned = _rewrite_trig_inverses(cleaned)  # ^-1 BEFORE general powers (60)
    cleaned = _rewrite_trig_powers(cleaned)
    cleaned = _rewrite_infinity(cleaned)
    cleaned = cleaned.replace("^", "**")  # generic caret conversion, always last
    _validate_parseable(cleaned, expression)
    return cleaned


def _matching_paren(expr: str, open_idx: int) -> int | None:
    """Index of the ``)`` closing the ``(`` at open_idx, or None if unbalanced."""
    depth = 0
    for i in range(open_idx, len(expr)):
        if expr[i] == "(":
            depth += 1
        elif expr[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return None


def _rewrite_log_bases(expr: str) -> str:
    """``logN(arg)`` -> ``log(arg, N)`` for bases other than 10 and 2."""
    pos = 0
    while (match := _LOG_BASE.search(expr, pos)) is not None:
        base = match.group(1)
        if base in ("10", "2"):
            pos = match.end()
            continue
        open_idx = match.end() - 1
        close_idx = _matching_paren(expr, open_idx)
        if close_idx is None:
            break  # unbalanced; the parse check will reject it
        arg = expr[open_idx + 1 : close_idx]
        expr = expr[: match.start()] + f"log({arg}, {base})" + expr[close_idx + 1 :]
        pos = match.start() + len("log(")  # rescan inside arg for nested forms
    return expr


def _rewrite_trig_inverses(expr: str) -> str:
    """``sin^-1(arg)`` -> ``asin(arg)`` (likewise cos, tan)."""
    while (match := _TRIG_INVERSE.search(expr)) is not None:
        open_idx = match.end() - 1
        close_idx = _matching_paren(expr, open_idx)
        if close_idx is None:
            break
        arg = expr[open_idx + 1 : close_idx]
        expr = expr[: match.start()] + f"a{match.group(1)}({arg})" + expr[close_idx + 1 :]
    return expr


def _rewrite_trig_powers(expr: str) -> str:
    """``sin^n(arg)`` -> ``sin(arg)**n`` (likewise cos, tan; any power)."""
    while (match := _TRIG_POWER.search(expr)) is not None:
        func, power = match.group(1), match.group(2)
        open_idx = match.end() - 1
        close_idx = _matching_paren(expr, open_idx)
        if close_idx is None:
            break
        arg = expr[open_idx + 1 : close_idx]
        expr = expr[: match.start()] + f"{func}({arg})**{power}" + expr[close_idx + 1 :]
    return expr


def _rewrite_infinity(expr: str) -> str:
    """``inf`` -> ``float('inf')``; a whole-expression ``-inf`` -> ``float('-inf')``."""
    if _WHOLE_NEG_INF.fullmatch(expr):
        return "float('-inf')"
    return _STANDALONE_INF.sub("float('inf')", expr)


def _validate_parseable(cleaned: str, original: str) -> None:
    """Raise CleanerError unless SymPy can parse the cleaned expression.

    Uses only the standard parser transformations — implicit multiplication is
    deliberately NOT enabled, so ``2x`` fails here instead of being guessed.
    ``float`` is provided so the infinity outputs ``float('inf')`` /
    ``float('-inf')`` parse successfully.
    """
    try:
        parse_expr(
            cleaned,
            transformations=standard_transformations,
            local_dict={"float": float},
        )
    except Exception as exc:
        raise CleanerError(f"Cannot parse expression: {original}") from exc
