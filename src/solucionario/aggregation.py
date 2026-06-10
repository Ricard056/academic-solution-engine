"""Component Aggregation stage (post-solve, pre-Extended-JSON).

Groups solved exercises by (id, id_letter); for each VALID component group it
writes the IDENTICAL results.component object onto every member (bible 90/75):

- total_value      float sum of member numeric_value
- total_latex      sympy.latex of the symbolic sum
- operation        "sum" (the only Phase 1 operation)
- operation_latex  members' solution_latex joined with " + " in id_component order

Symbolic values come from results["_symbolic_result"] via sympify — the
internal in-memory handoff written by the solver and stripped before
serialization (the Extended JSON stage owns the strip and its schema-closure
test). Aggregation never re-solves integrals, never parses solution_latex,
and never reconstructs exact symbolic totals from numeric_value floats.

This is NOT a solver, and the render adapter never computes totals.

Copy-on-write: returns a new list in the original input order. Aggregated
members are replaced by shallow-copied exercises with shallow-copied results;
everything else passes through by reference, untouched. Groups that cannot be
aggregated (structural problems per validation.validate_group(), non-component
modes, failed or unsolved members) pass through UNCHANGED: they are
represented by the ABSENCE of results.component — never by an invented marker
field, so Extended JSON stays bible-75 canonical. Later stages re-derive the
why (validate_group + results.status) and surface one kind:"error" item.

No formatting here: no decimal_string, no units, no render items, no document
metadata.
"""

import sympy

from solucionario.ids import MODE_COMPONENT, group_exercises, group_mode
from solucionario.validation import validate_group


def aggregate_components(exercises: list[dict]) -> list[dict]:
    """Run the Component Aggregation stage over solved exercises.

    Pure and order-preserving; see the module docstring for the contract.
    """
    replacements: dict[int, dict] = {}

    for _key, members in group_exercises(exercises):
        if not _aggregatable(members):
            continue
        component = _build_component(members)  # ONE shared object per group
        for member in members:
            new_results = dict(member["results"])
            new_results["component"] = component
            replacement = dict(member)
            replacement["results"] = new_results
            replacements[id(member)] = replacement

    return [replacements.get(id(exercise), exercise) for exercise in exercises]


def _aggregatable(members: list[dict]) -> bool:
    """True only when summing this group is safe (bible 90)."""
    if group_mode(members) != MODE_COMPONENT:
        return False  # standard/output/incoherent groups never aggregate
    if validate_group(members) is not None:
        return False  # structurally invalid: must not attempt to sum
    for member in members:
        results = member.get("results")
        if not isinstance(results, dict):
            return False  # unsolved member; nothing to sum
        if results.get("status") == "error":
            return False  # failed member -> whole group errors downstream
        if "_symbolic_result" not in results or "numeric_value" not in results:
            return False  # missing solve data; cannot sum safely
    return True


def _build_component(members: list[dict]) -> dict:
    """Build the bible-75 component object. members arrive ordered by
    id_component (ids.group_exercises sorts them)."""
    symbolic_total = sympy.Add(
        *[sympy.sympify(m["results"]["_symbolic_result"]) for m in members]
    )
    return {
        "total_value": float(sum(m["results"]["numeric_value"] for m in members)),
        "total_latex": sympy.latex(symbolic_total),
        "operation": "sum",
        "operation_latex": " + ".join(m["results"]["solution_latex"] for m in members),
    }
