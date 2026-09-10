"""T021: kill mid-workflow, confirm state intact. Written test-first; xfail
until Group 17 (T059 reaper) + T077 (restart recovery routine) land, per
tasks.md's explicit design (a task written early, satisfied later — same
pattern as this project's own reconciliation work).
"""
import pytest


@pytest.mark.xfail(reason="depends on T059 (Group 17) + T077 (Group 24), not yet implemented", strict=False)
def test_running_stage_forced_to_failed_transient_on_restart(tmp_path, monkeypatch):
    import src.persistence.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    conn = db_module.get_connection()
    db_module.init_schema(conn)

    from src.orchestration.scheduler import recover_on_startup  # not yet implemented

    conn.execute(
        "INSERT INTO orchestration_workflow_instance VALUES (?,?,?,?,?,?)",
        ("wf1", "test", "n/a", "running", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
    )
    conn.execute(
        "INSERT INTO orchestration_workflow_stage VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "stage1", "wf1", "some_stage", "running", 1, "idempotent",
            "rev1", None, None, 30, "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z",
        ),
    )
    conn.commit()

    recover_on_startup(conn)

    row = conn.execute(
        "SELECT status FROM orchestration_workflow_stage WHERE id='stage1'"
    ).fetchone()
    assert row["status"] == "failed_transient"
    conn.close()
