"""T074: infeasible-rollback case must use compensation, never claim rollback."""
from src.orchestration.compensation import dispatch


def test_uncommitted_transaction_rolls_back():
    assert dispatch("uncommitted_transaction") == "rolled_back"


def test_externally_observed_effect_must_compensate_not_rollback():
    assert dispatch("externally_observed") == "compensated"
