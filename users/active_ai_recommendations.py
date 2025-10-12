# routers/ai_recommendations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from deps import get_current_user  # adjust import paths
from models import ActiveTripAIRecommendation
from schemas import (
    ActiveAIRecommendationCreate,
    ActiveAIRecommendationOut,
    ActiveAIRecommendationUpdate,
)
from models import User, Trip  # adjust imports
from database import  get_db

router = APIRouter(prefix="/active_ai-recommendations", tags=["ai-recommendations"])

@router.post("/", response_model=ActiveAIRecommendationOut, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    payload: ActiveAIRecommendationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = ActiveTripAIRecommendation(
        rec_id=payload.rec_id,
        title=payload.title,
        destination=payload.destination,
        category=payload.category,
        cover_image=payload.cover_image,
        images=payload.images or [],
        description=payload.description,
        cultural_tips=payload.cultural_tips or [],
        location=payload.location.dict() if payload.location else None,
        best_time=payload.best_time,
        estimated_cost=payload.estimated_cost,
        popularity=payload.popularity or 0,
        rating=payload.rating or 0.0,
        in_itinerary=1 if payload.in_itinerary else 0,
        user_id=current_user.id,
        trip_id=payload.trip_id
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/current_trip/{trip_id}", response_model=List[ActiveAIRecommendationOut])
def list_recommendations_for_user(
    trip_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(ActiveTripAIRecommendation).filter(ActiveTripAIRecommendation.trip_id == trip_id)
    results = q.order_by(ActiveTripAIRecommendation.created_at.desc()).all()    
    return results


@router.get("/{rec_id}", response_model=ActiveAIRecommendationOut)
def get_recommendation(rec_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = db.query(ActiveTripAIRecommendation).filter(ActiveTripAIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    # optionally ensure user owns it
    if rec.user_id and rec.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this recommendation")
    return rec


@router.patch("/{rec_id}", response_model=ActiveAIRecommendationOut)
def update_recommendation(rec_id: int, payload: ActiveAIRecommendationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = db.query(ActiveTripAIRecommendation).filter(ActiveTripAIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.user_id and rec.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Apply updates
    for field, val in payload.dict(exclude_unset=True).items():
        if field == "in_itinerary":
            setattr(rec, "in_itinerary", 1 if val else 0)
        else:
            setattr(rec, field, val)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{rec_id}", status_code=status.HTTP_200_OK)
def delete_recommendation(rec_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = db.query(ActiveTripAIRecommendation).filter(ActiveTripAIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.user_id and rec.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(rec)
    db.commit()
    return {"detail": "Recommendation deleted"}