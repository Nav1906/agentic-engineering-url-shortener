"""Real credential provisioning (T100; ADR-0006 Revision 5).

Human Gate 4 decision, 2026-09-11: a scope-limited ADR-0006 Revision 5 was
adopted. This prototype MUST NOT launch Claude Code or any external agent
subprocess — external-agent execution stays permanently fail-closed (see
src/orchestration/adapters/launcher.py, T102). That removal is what makes
a real credential-provisioning path safe to build now: there is no agent
process for a same-OS-user credential-isolation gap to matter to, because
no agent process is ever launched. This module does NOT claim same-user
macOS credential isolation is solved — see docs/threat-model.md.

Storage design:
- Raw tokens: `local-secrets/approval_tokens.raw.json`, chmod 600,
  gitignored, printed to stdout exactly once at creation time.
- Token hashes (the "application configuration" the running app reads):
  `local-secrets/approval_tokens.hashed.json` — also gitignored. A hash
  file leaking is far less severe than a raw-token leak, but it is still
  gitignored per explicit instruction, since it's tied to local
  credentials and never belongs in version control regardless.
- Both files live under `local-secrets/`, the same directory this project
  reserved (and kept empty) since the original ADR-0006 rejection.

`LOCAL_SECRETS_DIR` is a module attribute (not a baked-in constant) so
tests can monkeypatch it to an isolated tmp_path, the same pattern
src/persistence/db.py::DB_PATH already uses — this keeps the real project
checkout's own local-secrets/ directory untouched by the test suite.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Role = Literal["reviewer_approver", "release_owner"]

_REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_SECRETS_DIR = _REPO_ROOT / "local-secrets"

TOKEN_BYTES = 32  # 256 bits of entropy, per role/identity


def raw_tokens_path() -> Path:
    return LOCAL_SECRETS_DIR / "approval_tokens.raw.json"


def hashed_config_path() -> Path:
    return LOCAL_SECRETS_DIR / "approval_tokens.hashed.json"


@dataclass(frozen=True)
class ProvisionedIdentity:
    identity: str
    role: Role


DEFAULT_IDENTITIES: tuple[ProvisionedIdentity, ...] = (
    ProvisionedIdentity("alice", "reviewer_approver"),
    ProvisionedIdentity("bob", "release_owner"),
)


def _hash_token(token: str, salt: str) -> str:
    return hashlib.sha256((salt + token).encode()).hexdigest()


def bootstrap(
    identities: tuple[ProvisionedIdentity, ...] = DEFAULT_IDENTITIES,
    force: bool = False,
) -> dict[str, str]:
    """T100: generates one cryptographically random token per identity,
    writes raw tokens (chmod 600) and a separate hash-only config, and
    returns the raw tokens ONCE so the caller (scripts/bootstrap_credentials.py)
    can print them. There is no read-back path for raw tokens outside
    read_raw_token() (T101's local CLI use) — this function itself is the
    only place a freshly-generated raw token is ever returned in memory."""
    hashed_path = hashed_config_path()
    if hashed_path.exists() and not force:
        raise FileExistsError(
            f"{hashed_path} already exists — refusing to overwrite existing "
            "credentials without force=True (this would invalidate every token already "
            "handed to an operator)"
        )

    LOCAL_SECRETS_DIR.mkdir(parents=True, exist_ok=True)

    raw_tokens: dict[str, str] = {}
    hashed_config: dict[str, dict[str, str]] = {}
    for provisioned in identities:
        token = secrets.token_urlsafe(TOKEN_BYTES)
        salt = secrets.token_hex(16)
        raw_tokens[provisioned.identity] = token
        hashed_config[provisioned.identity] = {
            "role": provisioned.role,
            "salt": salt,
            "token_hash": _hash_token(token, salt),
        }

    raw_path = raw_tokens_path()
    with open(raw_path, "w") as f:
        json.dump(raw_tokens, f, indent=2)
    os.chmod(raw_path, stat.S_IRUSR | stat.S_IWUSR)  # chmod 600

    with open(hashed_path, "w") as f:
        json.dump(hashed_config, f, indent=2)
    os.chmod(hashed_path, stat.S_IRUSR | stat.S_IWUSR)  # chmod 600, same posture

    return raw_tokens


def load_hashed_config() -> dict[str, dict[str, str]]:
    """The real credential store the running application reads. Returns
    {} if bootstrap has never been run — fail-closed, same posture as
    before T100, just now with a real (optional) path to leave it."""
    hashed_path = hashed_config_path()
    if not hashed_path.exists():
        return {}
    with open(hashed_path) as f:
        return json.load(f)


def verify_token(bearer_token: str) -> tuple[str, Role] | None:
    """Verifies a presented token against every stored hash using a
    constant-time comparison. Returns (identity, role) on success, None
    otherwise — never raises for an invalid token, since rejection is the
    expected, common outcome."""
    config = load_hashed_config()
    for identity, entry in config.items():
        candidate_hash = _hash_token(bearer_token, entry["salt"])
        if hmac.compare_digest(candidate_hash, entry["token_hash"]):
            return identity, entry["role"]  # type: ignore[return-value]
    return None


def read_raw_token(identity: str) -> str:
    """T101: the ONLY intended reader of the raw-token file — the
    human-invoked approval CLI (scripts/approve.py), running locally as
    the same operator who ran bootstrap. Never called from any HTTP
    request-handling code path."""
    raw_path = raw_tokens_path()
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} does not exist — run scripts/bootstrap_credentials.py first"
        )
    with open(raw_path) as f:
        raw = json.load(f)
    if identity not in raw:
        raise KeyError(f"no provisioned token for identity {identity!r}")
    return raw[identity]
