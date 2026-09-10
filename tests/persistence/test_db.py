"""T019: connection helper WAL mode + busy_timeout (FR-109, FR-110)."""
import src.persistence.db as db_module


def test_wal_mode_and_busy_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    conn = db_module.get_connection()
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert timeout == db_module.BUSY_TIMEOUT_MS
    finally:
        conn.close()


def test_init_schema_creates_all_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    conn = db_module.get_connection()
    try:
        db_module.init_schema(conn)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {r[0] for r in rows}
        expected = {
            "domain_short_link",
            "domain_idempotency_record",
            "domain_analytics_outbox",
            "applied_events",
            "analytics_system_status",
            "domain_short_link_analytics_summary",
            "orchestration_workflow_instance",
            "orchestration_workflow_stage",
            "orchestration_stage_execution",
            "orchestration_stage_dependency",
            "orchestration_decision_lineage",
            "orchestration_approval_decision",
            "policy_evaluation",
            "policy_exception",
            "audit_events",
        }
        assert expected.issubset(table_names)
    finally:
        conn.close()
