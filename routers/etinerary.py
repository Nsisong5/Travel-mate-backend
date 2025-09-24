from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from deps import get_current_user
from database import get_db
from Schemas.etinerary import (
  EtineraryCreate, EtineraryRead)
from Models.etinerary import Etinerary
import json
import models 


router = APIRouter(prefix="/trip", tags=["Etinerary"])


@router.get("/trip/etineraries/{trip_id}", response_model=list[EtineraryRead])
def get_etineraries(
  trip_id: int,
  db: Session = Depends(get_db),
  user: models.User = Depends(get_current_user)):
  try:
      etineraries = db.query(Etinerary).filter(Etinerary.trip_id == trip_id).all()
      print(etineraries)
      if not etineraries:
        raise HTTPException(status_code=400, detail="no etinerary for this trip")
      for itinerary in etineraries:
           itinerary.items = json.loads(itinerary.items)
      return etineraries 
      
  except Exception as e:
       raise HTTPException(status_code=422, detail={"Error during fetching etineraries":e})
  return []
  


@router.post("/etineraries", response_model=EtineraryRead)
def get_etineraries(
  etinerary: EtineraryCreate,
  db: Session = Depends(get_db),
  user: models.User = Depends(get_current_user)
):

  new_etinerary = Etinerary(
      day = etinerary.day,
      title = etinerary.title,
      trip_id = etinerary.trip_id,
      items = json.dumps(etinerary.items)
 )
  
  try:
       db.add(new_etinerary)
       db.commit()
       db.refresh(new_etinerary)
       new_etinerary.items = json.loads(new_etinerary.items) 
       return new_etinerary 
  except Exception as e:
      raise HTTPException(status_code=500, detail={"error": e })




@router.patch("/etineraries/{id}", response_model=EtineraryRead)
def update_etinerary(
  id: int,
  etinerary: EtineraryCreate,
  db: Session = Depends(get_db),
  user: models.User = Depends(get_current_user)
):
  db_etinerary = db.query(Etinerary).filter(Etinerary.id == id). first()
  if not db_etinerary:
        raise HTTPException(status_code=404, detail="Etinerary not found")
  
  
  update_data = etinerary.dict(exclude_unset=True)
  for key, value in update_data.items():
        if type(value) == list:
            value = json.dumps(value)
            setattr(db_etinerary, key, value)         
        setattr(db_etinerary, key, value)
        

  db.add(db_etinerary)
  db.commit()
  db.refresh(db_etinerary)
  db_etinerary.items = json.loads(db_etinerary.items)
  return db_etinerary  
  
  
@router.delete("/etineraries/{etinerary_id}", status_code=204)
def delete_yearly_budget(etinerary_id: int, db: Session = Depends(get_db),
     user: models.User = Depends(get_current_user)):
    """
    Deletes a yearly budget entry.
    """
    db_etinerary = db.query(Etinerary).filter(Etinerary.id == etinerary_id).first()
    if not db_etinerary:
        raise HTTPException(status_code=404, detail="Etinerary not found")

    db.delete(db_etinerary)
    db.commit()
    return {"message": "Etinerary deleted successfully"}



@router.get("/etineraries/{id}",response_model=EtineraryRead)    
def get_etinerary(
  id: int,
  db: Session = Depends(get_db),
  user: models.User = Depends(get_current_user)
):
  
  it = db.query(Etinerary).filter(Etinerary.id == id).first()
  if not it:
       raise HTTPException(status_code=404, detail="itinerary not found")
       
  it.items = json.loads(it.items)
  return it