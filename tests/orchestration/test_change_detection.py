"""T055: material-change detector, all 6 listed change types, none exempted."""
import pytest

from src.orchestration.replanning import classify_change


@pytest.mark.parametrize(
    "change_type",
    ["requirements", "architecture", "schema", "workflow_states", "security_controls", "release_criteria"],
)
def test_all_six_types_classified_material(change_type):
    assert classify_change(change_type) is True


def test_unlisted_type_not_material():
    assert classify_change("cosmetic_rename") is False
