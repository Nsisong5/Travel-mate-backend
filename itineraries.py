from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database

router = APIRouter(
    prefix="/itineraries",
    tags=["Itineraries & Activities"]
)

get_db = database.get_db


# ----------- Itinerary Endpoints -----------

@router.post("/", response_model=schemas.Itinerary)
def create_itinerary(trip_id: int, itinerary: schemas.ItineraryCreate, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    new_itinerary = models.Itinerary(**itinerary.dict(), trip_id=trip_id)
    db.add(new_itinerary)
    db.commit()
    db.refresh(new_itinerary)
    return new_itinerary


@router.get("/{trip_id}", response_model=List[schemas.Itinerary])
def get_itineraries(trip_id: int, db: Session = Depends(get_db)):
    return db.query(models.Itinerary).filter(models.Itinerary.trip_id == trip_id).all()


@router.put("/{itinerary_id}", response_model=schemas.Itinerary)
def update_itinerary(itinerary_id: int, itinerary: schemas.ItineraryCreate, db: Session = Depends(get_db)):
    db_itinerary = db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    if not db_itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    for key, value in itinerary.dict().items():
        setattr(db_itinerary, key, value)

    db.commit()
    db.refresh(db_itinerary)
    return db_itinerary


@router.delete("/{itinerary_id}")
def delete_itinerary(itinerary_id: int, db: Session = Depends(get_db)):
    db_itinerary = db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    if not db_itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    db.delete(db_itinerary)
    db.commit()
    return {"message": "Itinerary deleted successfully"}


# ----------- Activity Endpoints -----------

@router.post("/{itinerary_id}/activities", response_model=schemas.Activity)
def create_activity(itinerary_id: int, activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    itinerary = db.query(models.Itinerary).filter(models.Itinerary.id == itinerary_id).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    new_activity = models.Activity(**activity.dict(), itinerary_id=itinerary_id)
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


@router.get("/{itinerary_id}/activities", response_model=List[schemas.Activity])
def get_activities(itinerary_id: int, db: Session = Depends(get_db)):
    return db.query(models.Activity).filter(models.Activity.itinerary_id == itinerary_id).all()


@router.put("/activities/{activity_id}", response_model=schemas.Activity)
def update_activity(activity_id: int, activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    db_activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    for key, value in activity.dict().items():
        setattr(db_activity, key, value)

    db.commit()
    db.refresh(db_activity)
    return db_activity


@router.delete("/activities/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    db_activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(db_activity)
    db.commit()
    return {"message": "Activity deleted successfully"}