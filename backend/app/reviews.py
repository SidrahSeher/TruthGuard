from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db.models import AuditEntry, Review

PENDING = "Pending Review"
APPROVED = "Approved"
EDITED = "Edited & Approved"
REJECTED = "Rejected"
STATUS_FOR_ACTION = {"approve": APPROVED, "reject": REJECTED, "edit": EDITED}


class AlreadyDecided(Exception):
    """A review item can be decided only once."""


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt) -> str:
    return dt.replace(tzinfo=None).isoformat() + "Z" if dt else ""


def pick_claim(analysis: dict) -> dict:
    """The claim to put in front of a human: the most serious one."""
    claims = analysis.get("detectors", {}).get("hallucination", {}).get("claims", [])
    for status in ("Contradicted", "Insufficient evidence"):
        for claim in claims:
            if claim.get("status") == status:
                return claim
    return {"text": analysis.get("answer", ""), "reason": "", "evidence": ""}


def new_review(run_id: int, analysis: dict) -> Review:
    """The automatic review item for a Critical run."""
    claim = pick_claim(analysis)
    return Review(
        run_id=run_id,
        claim_text=claim.get("text", ""),
        ai_assessment="; ".join(analysis["risk"]["reasons"]) or claim.get("reason", ""),
        evidence=claim.get("evidence") or analysis.get("evidence", ""),
        risk_level=analysis["risk"]["level"],
    )


def forward_review(session, run, analysis: dict, claim_text: str) -> Review:
    """A review item that the user sent in by hand."""
    claims = analysis.get("detectors", {}).get("hallucination", {}).get("claims", [])
    match = next((c for c in claims if c.get("text") == claim_text), None) or {}
    review = Review(
        run_id=run.id,
        claim_text=claim_text,
        ai_assessment=match.get("reason") or "Sent to human review by the user",
        evidence=match.get("evidence") or run.evidence or "",
        risk_level=run.risk_level or "",
    )
    session.add(review)
    session.add(AuditEntry(run_id=run.id, topic=run.question, score=run.risk_score,
                           status="Claim sent to human review", reviewer="User"))
    return review


def decide(session, review, run, action: str, notes: str = "", reviewer: str = "",
           edited_answer: str = "") -> None:
    if review.status != PENDING:
        raise AlreadyDecided("This item has already been decided")
    if action not in STATUS_FOR_ACTION:
        raise ValueError("Unknown action")
    if action == "edit" and not edited_answer.strip():
        raise ValueError("An edited answer is required")
    review.status = STATUS_FOR_ACTION[action]
    review.notes = notes
    review.reviewer = reviewer.strip() or "Reviewer"
    review.edited_answer = edited_answer.strip() if action == "edit" else ""
    review.decided_at = _now()
    session.add(AuditEntry(
        run_id=review.run_id,
        topic=run.question if run else "",
        score=run.risk_score if run else None,
        status=f"Human review: {review.status}",
        reviewer=review.reviewer,
    ))


def release_state(run, run_reviews: list):
    """What the end user may see. A Critical answer stays withheld until a human approves it.
    The first (automatic) review of the run is the gate. Returns (state, final_answer)."""
    if run.risk_level != "Critical":
        return "released", run.answer
    if not run_reviews:
        return "withheld", None
    gate = min(run_reviews, key=lambda r: r.id)
    if gate.status == APPROVED:
        return "released", run.answer
    if gate.status == EDITED:
        return "released", gate.edited_answer
    if gate.status == REJECTED:
        return "blocked", None
    return "withheld", None


def review_json(review, run) -> dict:
    return {
        "id": review.id,
        "run_id": review.run_id,
        "question": run.question if run else "",
        "answer": run.answer if run else "",
        "claim_text": review.claim_text,
        "ai_assessment": review.ai_assessment,
        "evidence": review.evidence,
        "risk_level": review.risk_level,
        "risk_score": run.risk_score if run else None,
        "status": review.status,
        "notes": review.notes,
        "edited_answer": review.edited_answer,
        "reviewer": review.reviewer,
        "created_at": iso(review.created_at),
        "decided_at": iso(review.decided_at),
    }


def count_pending() -> int:
    with SessionLocal() as session:
        return session.query(Review).filter(Review.status == PENDING).count()