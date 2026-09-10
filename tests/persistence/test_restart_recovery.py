"""T021 (satisfied by T077): kill mid-workflow, confirm state intact.
Originally written test-first and marked xfail pending T059 (Group 17) +
T077 (Group 24); T077's recover_on_startup now exists and this test
genuinely passes — xfail marker removed accordingly (2026-09-10)."""


def test_running_stage_forced_to_failed_transient_on_restart(tmp_path, monkeypatch):
    import src.persistence.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    conn = db_module.get_connection()
    db_module.init_schema(conn)

    from src.orchestration.scheduler import recover_on_startup

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
