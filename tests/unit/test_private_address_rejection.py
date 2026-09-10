"""T042: private/internal-address rejection at creation time (plan.md §8)."""
import pytest

from src.domain.validation import ValidationError, validate_destination_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/internal",
        "http://192.168.1.1/router",
    ],
)
def test_rejects_private_or_loopback_literals(url):
    with pytest.raises(ValidationError):
        validate_destination_url(url)


def test_accepts_public_address():
    validate_destination_url("https://1.1.1.1/")
