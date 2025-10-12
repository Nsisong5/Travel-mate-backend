from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from database import get_db
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter 
import models 
from sqlalchemy.orm import Session
import schemas
import json 


router = APIRouter()


@router.post(
    "/travel-tips/", 
    response_model=schemas.TravelTipsResponse, 
    status_code=status.HTTP_201_CREATED
)
def create_travel_tips(data: schemas.TravelTipsCreate, db: Session = Depends(get_db)):
    """
    Endpoint to receive raw travel tips data, format it, and save it to the DB,
    linked to a specific trip_id.
    """
    # The core logic is delegated to the saving function
    db_tips = save_travel_tips_to_db(db, data.trip_id, data.raw_tips_data)

    # Format the response to match the Pydantic schema
    tips_content_dict = json.loads(db_tips.formatted_tips_json)
    return {
        "id": db_tips.id,
        "trip_id": db_tips.trip_id,
        # The tips_content key expects the FormattedTravelTips schema structure
        "tips_content": tips_content_dict
    }



@router.get(
    "/travel-tips/by-trip/{trip_id}", 
    response_model=schemas.TravelTipsResponse
)
def get_travel_tips_by_trip_id(trip_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to retrieve travel tips associated with a specific trip_id.
    Leverages the one-to-one relationship.
    """
    # Query the TravelTips table using the trip_id
    db_tips = db.query(models.TravelTips).filter(models.TravelTips.trip_id == trip_id).first()
    
    if db_tips is None:
        # Raise 404 if no travel tips are found for that trip ID
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Travel tips for Trip ID {trip_id} not found."
        )

    # Deserialize the JSON string back into a dictionary
    tips_content_dict = json.loads(db_tips.formatted_tips_json)

    # Format the response
    return {
        "id": db_tips.id,
        "trip_id": db_tips.trip_id,
        "tips_content": tips_content_dict
    }



@router.get(
    "/travel-tips/{tips_id}", 
    response_model=schemas.TravelTipsResponse
)
def get_travel_tips_by_id(tips_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to retrieve travel tips by their primary ID.
    """
    # Query the TravelTips table using its primary key (id)
    db_tips = db.query(TravelTips).filter(TravelTips.id == tips_id).first()
    
    if db_tips is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Travel tips with ID {tips_id} not found."
        )

    # Deserialize the JSON string back into a dictionary
    tips_content_dict = json.loads(db_tips.formatted_tips_json)

    # Format the response
    return {
        "id": db_tips.id,
        "trip_id": db_tips.trip_id,
        "tips_content": tips_content_dict
    }

