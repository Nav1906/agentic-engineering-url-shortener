"""Rollback vs. compensation dispatch (T074; FR-404, ADR-0007).

FR-404: rollback (technically reversing an action) is distinguished from
compensation (offsetting an action that cannot be reversed); compensation
MUST be used wherever rollback is not technically feasible. Claiming
rollback for an infeasible case is a specification violation, not a
simplification — this module's dispatch function makes that impossible by
construction: an infeasible-rollback stage can only reach 'compensated',
never 'rolled_back'.
"""
from __future__ import annotations

from typing import Literal

Outcome = Literal["rolled_back", "compensated"]


def dispatch(operation_class: Literal["uncommitted_transaction", "externally_observed"]) -> Outcome:
    """uncommitted_transaction: rollback is technically feasible (nothing
    external has observed the effect yet) -> 'rolled_back'.
    externally_observed: the effect has already been observed outside this
    process's transactional boundary (e.g. an analytics count already
    drained, a redirect already issued) -> rollback is infeasible by
    construction -> 'compensated', never 'rolled_back'."""
    if operation_class == "uncommitted_transaction":
        return "rolled_back"
    return "compensated"
