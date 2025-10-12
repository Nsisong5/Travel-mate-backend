
from fastapi import HTTPException, Depends, Query, APIRouter,Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from deps import get_current_user
from database import get_db
import models
import schemas



def get_trips(
  user_id,
  db: Session, 
): 
   try:
        trips = db.query(models.Trip).filter(
            models.Trip.user_id == user_id
        ).all()
        return get_dict(trips)
   except Exception as e:
        # Better to re-raise or handle logging here, as it's not an endpoint
        print(f"Error fetching trips for user {user_id}: {e}")
        return [] # Return empty list on failure
        
        

    
def get_dict(trips_objects): 
   trips_data = []  
   for trip in trips_objects:
      trip_dict = {
            column.key: getattr(trip, column.key)
            for column in trip.__table__.columns
        }
      trips_data.append(trip_dict)
        
   return trips_data
    