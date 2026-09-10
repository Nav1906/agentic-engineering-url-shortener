# Phase 1 Data Model: Agentic Software Engineering System: URL Shortener

**Feature**: [spec.md](./spec.md) | **Depends on**: research.md, `docs/adr/0001`–`0010` (all Proposed)
**Storage**: single SQLite file, WAL mode (ADR-0003)

Every entity below traces to a Key Entity in spec.md and the FR(s) that define
its validation rules. Field types are SQLite-native (`TEXT`, `INTEGER`,
`REAL`); no ORM is assumed (ADR-0002/0003) but any implementation may use one
without changing this model's meaning.

---

## Domain package (`domain_*` tables, ADR-0001)

### `domain_short_link`

| Field | Type | Constraints / Validation | Source |
|---|---|---|---|
| `short_code` | TEXT | PRIMARY KEY, 7-char base62 (ADR-0004) | FR-102 |
| `destination_url` | TEXT | NOT NULL, validated scheme (allow-list) at write time | FR-101 |
| `created_at` | TEXT (ISO-8601) | NOT NULL | FR-101 |
| `expires_at` | TEXT (ISO-8601) | NULLABLE; if set, was validated strictly-future at creation time (FR-114) | FR-104 |
| `status` | TEXT | ENUM `active` / `deleted`; `expired` is *derived* at read time from `expires_at < now()`, never a stored status the app must remember to flip | FR-103, FR-104 |
| `deleted_at` | TEXT (ISO-8601) | NULLABLE | FR-104 (deletion path) |

**Validation rules**: `destination_url` scheme MUST be in the allow-list
(ADR pending in plan.md §8 Security — scheme allow-list itself is not a
separate ADR, it's a straightforward security control, detailed in plan.md).
`expires_at`, if present, MUST be strictly greater than `created_at` at
insert time (FR-114) — this check is **not** re-run on an idempotent replay
(FR-112).

**State transitions**: `active` → (time passes `expires_at`, derived, no
write) → *reads as expired*. `active` → `deleted` (explicit deletion,
irreversible — deletion does not remove the row, only sets `status` and
`deleted_at`, so idempotency records referencing it remain valid per FR-116).

### `domain_idempotency_record`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `idempotency_key` | TEXT | PRIMARY KEY | FR-112 |
| `validated_payload_hash` | TEXT | NOT NULL — hash of the syntax-validated creation request | FR-112, FR-113 |
| `short_code` | TEXT | NOT NULL, FOREIGN KEY → `domain_short_link.short_code` | FR-112 |
| `created_at` | TEXT (ISO-8601) | NOT NULL | FR-116 |

**Validation rules**: on a request with an existing key, syntax-validate the
incoming payload, hash it, compare to `validated_payload_hash`: match →
return `short_code`'s original result (FR-112); mismatch → `409` (FR-113).
**Retained indefinitely, independent of `domain_short_link.status`** (FR-116)
— never deleted when the referenced short link is deleted or expires.

### `domain_analytics_outbox` (ADR-0009 Rev. 3 — SQLite table, corrected ordering)

| Field | Type | Constraints | Source |
|---|---|---|---|
| `event_id` | TEXT (UUID) | PRIMARY KEY | ADR-0009 |
| `short_code` | TEXT | NOT NULL, FOREIGN KEY → `domain_short_link.short_code` | ADR-0009 |
| `redirected_at` | TEXT (ISO-8601) | NOT NULL | ADR-0009 |
| `drain_status` | TEXT | ENUM `pending` / `applied` | ADR-0009 |

Written in its own transaction **after** the HTTP redirect response has
already been sent (never before, and never in the same transaction as the
redirect-authorizing lookup) — corrected in Revision 3 to close an
overcount defect in the prior (withdrawn) pre-response write-ahead-log
design. Subject to ADR-0007's ordinary bounded-retry/`busy_timeout`
contention policy; no bespoke timeout, since this step is off the
response-latency-sensitive path entirely. Drained asynchronously by a
background task, idempotently by `event_id` (a check-and-insert against
`applied_events`, below, in the same transaction as the summary-count
increment — a crash mid-batch cannot double-count).

### `applied_events` (ADR-0009 Rev. 3)

| Field | Type | Constraints | Source |
|---|---|---|---|
| `event_id` | TEXT (UUID) | PRIMARY KEY | ADR-0009 |
| `applied_at` | TEXT (ISO-8601) | NOT NULL | ADR-0009 |

### `analytics_system_status` (ADR-0009 Rev. 3, schema; contract **approved** via spec.md FR-117, Human Gate 4, 2026-09-10)

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, always `1` | ADR-0009 |
| `state` | TEXT | ENUM `running` / `stopped_clean` | ADR-0009 |
| `started_at` | TEXT (ISO-8601) | NOT NULL | ADR-0009 |
| `clean_shutdown_at` | TEXT (ISO-8601) | NULLABLE | ADR-0009 |
| `degraded_since_unclean_shutdown_at` | TEXT (ISO-8601) | NULLABLE, **sticky** — set when a prior unclean shutdown is detected at startup; cleared only by an explicit, audited operator acknowledgment, never automatically. Per FR-117: acknowledgment clears only this field, never any `completeness_status` row already `incomplete` | FR-117, ADR-0009 |

Lives in the **same** SQLite database as every other table — deliberately,
so there is no second store that could fail independently of the events it
tracks (ADR-0009's answer to "what if event storage and loss-marker storage
fail independently": they can't, because they're the same store).

### `domain_short_link_analytics_summary`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `short_code` | TEXT | PRIMARY KEY, FOREIGN KEY → `domain_short_link.short_code` | FR-107 |
| `successful_redirect_count` | INTEGER | NOT NULL DEFAULT 0 | FR-105, FR-107 |
| `last_successful_redirect_at` | TEXT (ISO-8601) | NULLABLE (null until first success) | FR-107 |
| `completeness_status` | TEXT | ENUM `complete` / `degraded` / `incomplete` (ADR-0009 three-state model — elaborates FR-107's "at least" two states) | FR-107, ADR-0009 |

**State transitions** (ADR-0009 Rev. 3): `complete` ⇄ `degraded` (self-heals
as the outbox drains — the event was durably recorded, post-send, before
this state was ever reported, so no data was at risk in this transition);
`degraded`/`complete` → `incomplete` **one-way only**, set precisely when
the post-send outbox write itself observably fails after exhausting
ADR-0007's bounded retries — a *known* loss, distinct from the *unknown,
aggregate* possibility the system-wide `analytics_system_status.
degraded_since_unclean_shutdown_at` flag represents (**approved**, FR-117,
Human Gate 4 amendment, 2026-09-10). `complete` MUST NOT
be reported while that system-wide flag is set, regardless of this table's
own backlog state — an empty backlog never proves nothing was lost.

---

## Orchestration package (`orchestration_*` tables, ADR-0005)

### `orchestration_workflow_instance`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | TEXT (UUID) | PRIMARY KEY — **this is the correlation identifier** | FR-601 |
| `feature_ref` | TEXT | NOT NULL (e.g., `spec.md` requirement/scenario ID this run processes) | FR-204 |
| `scenario` | TEXT | ENUM `greenfield` / `brownfield` / `ambiguous` / `n/a` | FR-605 |
| `status` | TEXT | ENUM `running` / `awaiting_approval` / `safe_stopped` / `completed` / `rejected` | FR-201 |
| `created_at`, `updated_at` | TEXT (ISO-8601) | NOT NULL | FR-204 |

### `orchestration_workflow_stage`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | TEXT (UUID) | PRIMARY KEY | FR-203 |
| `workflow_instance_id` | TEXT | FOREIGN KEY → `orchestration_workflow_instance.id` | FR-201 |
| `name` | TEXT | NOT NULL | FR-203 |
| `status` | TEXT | ENUM `pending` / `ready` / `running` / `succeeded` / `failed_transient` / `failed_permanent` / `awaiting_approval` / `awaiting_reconciliation` / `rejected` / `skipped` | ADR-0005 Rev. 3 |
| `attempt_count` | INTEGER | DEFAULT 0 — incremented only inside the atomic claim statement (ADR-0005 Rev. 3), checked against the retry ceiling in the same statement | ADR-0007 |
| `effect_class` | TEXT | ENUM `idempotent` / `externally_observable_uncertain` — declared by the stage's adapter (ADR-0005 Rev. 3) | ADR-0005 |
| `artifact_revision` | TEXT | NOT NULL — the artifact revision this stage last ran/was approved against | FR-311, FR-501 |
| `preconditions`, `postconditions` | TEXT (JSON) | documentation fields, not enforced logic (enforcement is via `stage_dependency`) | FR-203 |
| `timeout_seconds` | INTEGER | NOT NULL, per ADR-0007 policy (with documented per-stage overrides) | FR-203, ADR-0007 |
| `created_at`, `updated_at` | TEXT (ISO-8601) | NOT NULL | FR-204 |

### `orchestration_stage_execution` (ADR-0005 Rev. 3)

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | TEXT (UUID) | PRIMARY KEY — the durable execution identity for one claim attempt | ADR-0005 |
| `stage_id` | TEXT | FOREIGN KEY → `orchestration_workflow_stage.id` | ADR-0005 |
| `attempt_number` | INTEGER | NOT NULL | ADR-0005 |
| `claimed_by_worker_id` | TEXT (UUID) | NOT NULL — process-instance identity, generated once at process startup | ADR-0005 |
| `claimed_at` | TEXT (ISO-8601) | NOT NULL | ADR-0005 |
| `lease_expires_at` | TEXT (ISO-8601) | NOT NULL — `claimed_at + max(stage.timeout_seconds, 30s)` | ADR-0005 |
| `workspace_path` | TEXT | NOT NULL for file-producing stages — the isolated `git worktree` path this execution's subprocess is confined to (ADR-0005, ADR-0006) | ADR-0005 |
| `status` | TEXT | ENUM `claimed` / `running` / `completed` / `failed` / `abandoned` | ADR-0005 |
| `outcome_detail` | TEXT (JSON) | NULLABLE — schema: `{validator_command, validator_exit_code, validator_output_hash, artifact_hashes: {path: sha256}}` (ADR-0005 Rev. 3) — a stage reaches `succeeded` only after the controller runs this validator and records this evidence; a clean `git status` or checked task box is explicitly not accepted on its own | ADR-0005 |

**Fencing rule** (ADR-0005): a completion write is
`UPDATE ... SET status='completed' WHERE id = :execution_id AND status IN
('claimed','running')` — a stale/zombie worker's late write affects 0 rows
once the reaper has already reconciled that execution, preventing a
duplicate or clobbered result.

**State transitions**: `pending` → `ready` (all `stage_dependency` rows
resolved) → `running` → `succeeded` \| `failed_transient` (→ retried, back to
`running`, bounded by ADR-0007) \| `failed_permanent` (→ `safe_stopped` at the
instance level, or a defined fallback stage). A stage found `running` at
process start (crash recovery, ADR-0005) is forced to `failed_transient`.
Any stage may be forced back to `pending` by a replanning event that
invalidates its `artifact_revision`.

### `orchestration_stage_dependency`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `workflow_instance_id` | TEXT | FOREIGN KEY | FR-201 |
| `stage_id` | TEXT | FOREIGN KEY → `orchestration_workflow_stage.id` | FR-201 |
| `depends_on_stage_id` | TEXT | FOREIGN KEY → `orchestration_workflow_stage.id` | FR-201 |

PRIMARY KEY `(stage_id, depends_on_stage_id)` — this table **is** the
explicit dependency graph (FR-201).

### `orchestration_decision_lineage`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT, append-only | FR-503 |
| `workflow_instance_id` | TEXT | FOREIGN KEY | FR-503 |
| `decision_type` | TEXT | e.g., `requirement_quality_check`, `ambiguity_detected`, `replanning_triggered` | FR-503 |
| `detail` | TEXT (JSON) | NOT NULL | FR-503 |
| `created_at` | TEXT (ISO-8601) | NOT NULL | FR-503 |

**Never UPDATEd or DELETEd** — append-only by application-code discipline
(ADR-0008).

### `orchestration_approval_decision`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | TEXT (UUID) | PRIMARY KEY | FR-310 |
| `workflow_instance_id` | TEXT | FOREIGN KEY | FR-301 |
| `gate_id` | TEXT | NOT NULL (e.g., `requirements_approval`, `release_readiness`) | FR-310 |
| `identity` | TEXT | NOT NULL — derived from verified credential, never caller-supplied (FR-308) | FR-308, FR-310 |
| `role` | TEXT | ENUM `reviewer_approver` / `release_owner` (FR-312) | FR-312 |
| `decision` | TEXT | ENUM `approved` / `rejected` / `escalated_timeout` | FR-302 |
| `rationale` | TEXT | NULLABLE | FR-310 |
| `artifact_revision` | TEXT | NOT NULL — the exact revision approved, binds this decision (FR-311) | FR-311 |
| `created_at` | TEXT (ISO-8601) | NOT NULL | FR-310 |
| `invalidated_at` | TEXT (ISO-8601) | NULLABLE — set by a replanning event when `artifact_revision` is superseded (FR-311) | FR-311 |

**Validation rule**: a `gate_id` of `release_readiness` or
`final_submission` MUST be matched with `role = release_owner`; all other
gates MUST be matched with `role = reviewer_approver` (FR-312, FR-313) — an
approval recorded under the wrong role for its gate is rejected before this
row is ever written.

---

## Policy package (`policy_*` tables)

### `policy_evaluation`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | FR-303 |
| `workflow_instance_id` | TEXT | FOREIGN KEY | FR-303 |
| `policy_id` | TEXT | NOT NULL (e.g., `dependency-scan`, `change-control`) | FR-303 |
| `policy_version` | TEXT | NOT NULL | FR-303 |
| `outcome` | TEXT | ENUM `PASS` / `FAIL` / `EXCEPTION-REQUESTED` / `NOT-APPLICABLE` | FR-303 |
| `evaluated_at` | TEXT (ISO-8601) | NOT NULL | FR-303 |

### `policy_exception`

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | TEXT (UUID) | PRIMARY KEY | FR-305 |
| `policy_evaluation_id` | INTEGER | FOREIGN KEY | FR-305 |
| `reason`, `scope` | TEXT | NOT NULL | FR-305 |
| `approving_identity` | TEXT | NOT NULL, verified credential (reuses ADR-0006's auth) | FR-305 |
| `compensating_control` | TEXT | NOT NULL | FR-305 |
| `approved_at` | TEXT (ISO-8601) | NOT NULL | FR-305 |
| `expires_at` | TEXT (ISO-8601) | NOT NULL — review/expiry condition | FR-305 |

---

## Audit package

### `audit_events` (ADR-0008, append-only)

| Field | Type | Constraints | Source |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | FR-602 |
| `workflow_instance_id` | TEXT | NULLABLE (some events are domain-only, e.g., a short-link creation outside any workflow) | FR-601 |
| `actor_type` | TEXT | ENUM `human` / `agent` / `system` | FR-602 |
| `action` | TEXT | NOT NULL | FR-602 |
| `timestamp` | TEXT (ISO-8601) | NOT NULL | FR-602 |
| `affected_artifact_or_state` | TEXT | NOT NULL | FR-602 |
| `result` | TEXT | NOT NULL | FR-602 |
| `reason` | TEXT | NOT NULL | FR-602 |
| `recovery_of_event_id` | INTEGER | NULLABLE, self-FK — links a recovery event to the failure it resolves (ADR-0008 MTTR definition) | ADR-0008 |
| `demonstration_flag` | INTEGER (bool) | NOT NULL — distinguishes demonstration/test runs from any other run, per FR-604 | FR-604 |
| `detail` | TEXT (JSON) | NULLABLE | FR-602 |

---

## Cross-cutting relationships

```
domain_short_link 1──* domain_idempotency_record   (a link may have been created via a key)
domain_short_link 1──1 domain_short_link_analytics_summary
domain_short_link 1──* domain_analytics_outbox   (written after response send, ADR-0009 Rev. 3)
domain_analytics_outbox 1──0..1 applied_events   (via event_id, drain dedup)
analytics_system_status (single row; same DB as everything else — ADR-0009 Rev. 3)
orchestration_workflow_instance 1──* orchestration_workflow_stage
orchestration_workflow_stage    *──* orchestration_workflow_stage   (via stage_dependency)
orchestration_workflow_stage    1──* orchestration_stage_execution   (one row per claim attempt, ADR-0005 Rev. 3)
orchestration_workflow_instance 1──* orchestration_decision_lineage
orchestration_workflow_instance 1──* orchestration_approval_decision
orchestration_workflow_instance 1──* policy_evaluation
policy_evaluation               1──0..1 policy_exception
(orchestration_workflow_instance | domain_*) 1──* audit_events
```

No cross-package table is written directly by another package's code — each
package owns its tables and exposes a narrow interface (ADR-0001).
