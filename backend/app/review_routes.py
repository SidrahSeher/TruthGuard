import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import reviews
from app.db.database import SessionLocal
from app.db.models import AuditEntry, Review, Run

router = APIRouter()


class ReviewForward(BaseModel):
    run_id: int
    claim_text: str = Field(min_length=1, max_length=2000)


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject", "edit"]
    notes: str = Field(default="", max_length=1000)
    reviewer: str = Field(default="Reviewer", max_length=80)
    edited_answer: str = Field(default="", max_length=5000)


@router.get("/api/reviews")
def list_reviews(status: str = "", limit: int = 200):
    limit = max(1, min(limit, 500))
    with SessionLocal() as session:
        query = session.query(Review)
        if status:
            query = query.filter(Review.status == status)
        rows = query.order_by(Review.id.desc()).limit(limit).all()
        return [reviews.review_json(r, session.get(Run, r.run_id)) for r in rows]


@router.post("/api/reviews")
def forward_claim(req: ReviewForward):
    with SessionLocal() as session:
        run = session.get(Run, req.run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        analysis = json.loads(run.analysis_json) if run.analysis_json else {}
        review = reviews.forward_review(session, run, analysis, req.claim_text)
        session.commit()
        return reviews.review_json(review, run)


@router.patch("/api/reviews/{review_id}")
def decide_review(review_id: int, req: ReviewDecision):
    with SessionLocal() as session:
        review = session.get(Review, review_id)
        if review is None:
            raise HTTPException(status_code=404, detail="Review not found")
        run = session.get(Run, review.run_id)
        try:
            reviews.decide(session, review, run, req.action, req.notes, req.reviewer,
                           req.edited_answer)
        except reviews.AlreadyDecided as error:
            raise HTTPException(status_code=409, detail=str(error))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))
        session.commit()
        return reviews.review_json(review, run)


@router.get("/api/audit")
def list_audit(limit: int = 200):
    limit = max(1, min(limit, 500))
    with SessionLocal() as session:
        rows = session.query(AuditEntry).order_by(AuditEntry.id.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "run_id": r.run_id,
                "topic": r.topic,
                "score": r.score,
                "status": r.status,
                "reviewer": r.reviewer,
                "timestamp": reviews.iso(r.timestamp),
            }
            for r in rows
        ]