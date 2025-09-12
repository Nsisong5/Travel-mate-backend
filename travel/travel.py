# routes/travel.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import database, auth

router = APIRouter(prefix="/travel", tags=["travel"])

@router.get("/distance")
def get_travel_distance(db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    # Mock distance for now
    mock_distance_km = 125.4  
    return {
        "user_id": current_user["id"],
        "total_distance_traveled_km": mock_distance_km,
        "note": "Mock data for now. Will integrate with Google Maps or Mapbox later."
    }