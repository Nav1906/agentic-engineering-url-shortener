"""Domain validation: URL scheme allow-list, expiry, private-address rejection.

T014 (FR-101, FR-114) + T042 (plan.md §8, private/internal-address rejection).

Allowed schemes (plan.md §8): https, http — PROPOSED, not yet finally
confirmed by the human candidate (plan.md §8 / tasks.md T014's open Risk
item). Implemented against this proposed list; do not treat as final.
"""
from __future__ import annotations

import ipaddress
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https", "http"}


class ValidationError(ValueError):
    """Raised for any rejected domain input (FR-101, FR-114, plan.md §8)."""


def validate_destination_url(url: str) -> None:
    if not url or not isinstance(url, str):
        raise ValidationError("destination URL must be a non-empty string")
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationError(
            f"scheme {parsed.scheme!r} is not in the allowed list {sorted(ALLOWED_SCHEMES)}"
        )
    if not parsed.netloc:
        raise ValidationError("destination URL must include a network location")
    _reject_private_or_internal_address(parsed.hostname)


def _reject_private_or_internal_address(hostname: str | None) -> None:
    """T042: creation-time-only check. Does NOT protect against DNS
    rebinding at resolution time — disclosed limitation, plan.md §8."""
    if not hostname:
        raise ValidationError("destination URL must include a hostname")
    candidates: list[str] = []
    try:
        candidates.append(str(ipaddress.ip_address(hostname)))
    except ValueError:
        try:
            infos = socket.getaddrinfo(hostname, None)
            candidates.extend(info[4][0] for info in infos)
        except socket.gaierror:
            # Unresolvable at creation time is not itself a rejection reason
            # here (it may become resolvable later); scheme/hostname-shape
            # checks above already ran.
            return
    for addr in candidates:
        ip = ipaddress.ip_address(addr)
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved:
            raise ValidationError(
                f"destination resolves to a private/internal/loopback address ({addr}); "
                "rejected at creation time (no DNS-rebinding protection at resolution time)"
            )


def validate_expires_at(expires_at: str | None) -> None:
    """FR-114: if supplied, must be a valid timestamp strictly in the future."""
    if expires_at is None:
        return
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"expiresAt is not a valid ISO-8601 timestamp: {expires_at!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed <= datetime.now(timezone.utc):
        raise ValidationError("expiresAt must be strictly in the future")
