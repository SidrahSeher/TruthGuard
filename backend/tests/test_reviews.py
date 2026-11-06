import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main, review_routes, reviews, service
from app.db import models  # noqa: F401  (makes the tables known)
from app.db.database import Base
from app.db.models import AuditEntry, Review

ANSWER = "Students must maintain at least 80% attendance."


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A fresh empty database for each test."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    for module in (main, review_routes, reviews, service):
        monkeypatch.setattr(module, "SessionLocal", session_factory)
    return session_factory


def analysis(level="Critical", score=80, status="Contradicted"):
    return {
        "question": "What is the attendance requirement?",
        "answer": ANSWER,
        "evidence": "Students must maintain at least 75% attendance.",
        "tool_calls": [{"tool": "document_search", "input": "q"}],
        "evidence_present": True,
        "detectors": {"hallucination": {"claims": [{
            "text": ANSWER, "status": status,
            "reason": "Answer says 80% but evidence says 75%",
            "evidence": "Students must maintain at least 75% attendance.",
        }]}},
        "risk": {"level": level, "score": score, "reasons": [
            "Hallucination: Answer says 80% but evidence says 75%",
            "Critical rule: a claim contradicts the evidence"]},
        "verification_score": 0.0,
        "steps": [{"step": "task_started", "detail": "q", "time": 0}],
    }


def first_review_id(client):
    return client.get("/api/reviews").json()[0]["id"]


def test_critical_run_creates_pending_review_and_audit(db):
    run_id = service._save(analysis(), "pasted")
    with db() as session:
        found = session.query(Review).all()
        audit = session.query(AuditEntry).all()
    assert len(found) == 1
    assert found[0].status == "Pending Review" and found[0].run_id == run_id
    assert len(audit) == 1
    assert audit[0].reviewer == "Automated" and audit[0].status == "Under Review"


def test_safe_run_has_audit_but_no_review(db):
    service._save(analysis("Safe", 0, "Supported"), "pasted")
    with db() as session:
        assert session.query(Review).count() == 0
        assert session.query(AuditEntry).one().status == "Safe"


def test_critical_answer_is_withheld_until_approved(db):
    run_id = service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        before = client.get(f"/api/runs/{run_id}").json()
        assert before["release"] == "withheld" and before["final_answer"] is None
        r = client.patch(f"/api/reviews/{first_review_id(client)}", json={"action": "approve"})
        assert r.status_code == 200 and r.json()["status"] == "Approved"
        after = client.get(f"/api/runs/{run_id}").json()
    assert after["release"] == "released" and after["final_answer"] == ANSWER


def test_reject_blocks_the_answer(db):
    run_id = service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        client.patch(f"/api/reviews/{first_review_id(client)}", json={"action": "reject"})
        run = client.get(f"/api/runs/{run_id}").json()
    assert run["release"] == "blocked" and run["final_answer"] is None


def test_edit_releases_the_edited_answer(db):
    run_id = service._save(analysis(), "pasted")
    fixed = "Students must maintain at least 75% attendance."
    with TestClient(main.app) as client:
        r = client.patch(f"/api/reviews/{first_review_id(client)}",
                         json={"action": "edit", "edited_answer": fixed, "reviewer": "Sir"})
        assert r.json()["status"] == "Edited & Approved"
        run = client.get(f"/api/runs/{run_id}").json()
    assert run["release"] == "released" and run["final_answer"] == fixed


def test_edit_without_text_is_rejected(db):
    service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        r = client.patch(f"/api/reviews/{first_review_id(client)}", json={"action": "edit"})
    assert r.status_code == 400


def test_cannot_decide_twice(db):
    service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        review_id = first_review_id(client)
        assert client.patch(f"/api/reviews/{review_id}", json={"action": "approve"}).status_code == 200
        assert client.patch(f"/api/reviews/{review_id}", json={"action": "reject"}).status_code == 409


def test_decision_is_written_to_the_audit_log(db):
    service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        client.patch(f"/api/reviews/{first_review_id(client)}",
                     json={"action": "approve", "reviewer": "Dr. Test", "notes": "Checked the rules"})
        log = client.get("/api/audit").json()
    assert log[0]["status"] == "Human review: Approved"
    assert log[0]["reviewer"] == "Dr. Test"
    assert log[1]["reviewer"] == "Automated"


def test_forwarding_a_claim_creates_a_pending_review(db):
    run_id = service._save(analysis("Safe", 0, "Supported"), "pasted")
    with TestClient(main.app) as client:
        r = client.post("/api/reviews", json={"run_id": run_id, "claim_text": ANSWER})
        assert r.status_code == 200 and r.json()["status"] == "Pending Review"
        run = client.get(f"/api/runs/{run_id}").json()
    assert run["release"] == "released"          # only Critical answers are held back


def test_forwarding_an_unknown_run_is_404(db):
    with TestClient(main.app) as client:
        r = client.post("/api/reviews", json={"run_id": 999, "claim_text": "x"})
    assert r.status_code == 404


def test_unknown_review_is_404(db):
    with TestClient(main.app) as client:
        assert client.patch("/api/reviews/999", json={"action": "approve"}).status_code == 404


def test_invalid_action_is_422(db):
    service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        r = client.patch(f"/api/reviews/{first_review_id(client)}", json={"action": "delete"})
    assert r.status_code == 422


def test_pending_filter_and_dashboard_count(db):
    service._save(analysis(), "pasted")
    service._save(analysis(), "pasted")
    with TestClient(main.app) as client:
        newest = first_review_id(client)
        client.patch(f"/api/reviews/{newest}", json={"action": "approve"})
        pending = client.get("/api/reviews", params={"status": "Pending Review"}).json()
        stats = client.get("/api/stats").json()
    assert len(pending) == 1
    assert stats["pending_reviews"] == 1