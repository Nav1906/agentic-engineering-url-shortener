"""T106: HTTP-only integration test. Creates a workflow through the real
API, with the real app's real lifespan (which starts the real asyncio
background scheduler) -- observes its real transitions purely by polling
GET /workflows/{id}, with ZERO direct calls into
src/orchestration/scheduler.py or live_scheduler.py from this test. If the
background loop weren't actually running and driving the DAG, this test
would time out, not silently pass.
"""
import time

from fastapi.testclient import TestClient


def test_workflow_progresses_automatically_to_completion(tmp_path, monkeypatch):
    import src.persistence.db as db_module
    from src.api.middleware.rate_limit import reset_all

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "app.db"))
    reset_all()
    from src.api.main import app

    with TestClient(app) as client:
        create = client.post("/workflows", json={"requirement": "demo", "auto_execute": True})
        assert create.status_code == 201
        wf_id = create.json()["id"]
        assert create.json()["status"] == "running"

        # Poll purely via HTTP -- no direct scheduler/tick call anywhere
        # in this test. Bounded wait: the real background loop ticks every
        # 0.2s (src/orchestration/live_scheduler.py::TICK_INTERVAL_SECONDS).
        deadline = time.monotonic() + 10.0
        final_status = None
        final_body = None
        while time.monotonic() < deadline:
            resp = client.get(f"/workflows/{wf_id}")
            assert resp.status_code == 200
            body = resp.json()
            if body["status"] in ("completed", "safe_stopped", "rejected"):
                final_status = body["status"]
                final_body = body
                break
            time.sleep(0.1)

        assert final_status is not None, "workflow never reached a terminal state within 10s"
        assert final_status == "completed", f"expected 'completed', got {final_status}: {final_body}"

        stage_by_name = {s["name"]: s["status"] for s in final_body["stages"]}
        assert stage_by_name["intake"] == "succeeded"
        assert stage_by_name["classify"] == "succeeded"
        assert stage_by_name["proceed_path"] == "succeeded"
        assert stage_by_name["hold_path"] == "skipped"

        # Confirm real transitions were actually observed over multiple
        # polls, not just a single lucky read (i.e. genuine progression,
        # not an instantaneous no-op).
        audit = client.get(f"/workflows/{wf_id}/audit-events")
        assert audit.status_code == 200
        actions = [e["action"] for e in audit.json()]
        assert "auto_execute_pipeline_seeded" in actions
        assert "branch_selected" in actions
        assert "branch_not_selected" in actions

        policy_evals = client.get(f"/workflows/{wf_id}/policy-evaluations")
        assert policy_evals.status_code == 200
        assert len(policy_evals.json()) == 3  # T105: all mandatory policies ran automatically
