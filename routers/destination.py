from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud.destination as crud
import Models.destination as models 
import Schemas.destination as schemas
from database import get_db

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.post("/", response_model=schemas.DestinationResponse)
def create_destination(destination: schemas.DestinationCreate, db: Session = Depends(get_db)):
    return crud.create_destination(db, destination)


@router.get("/", response_model=list[schemas.DestinationResponse])
def list_destinations(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.get_destinations(db, skip=skip, limit=limit)


@router.get("/{destination_id}", response_model=schemas.DestinationResponse)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    db_destination = crud.get_destination_by_id(db, destination_id)
    if not db_destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return db_destination


@router.put("/{destination_id}", response_model=schemas.DestinationResponse)
def update_destination(destination_id: int, destination: schemas.DestinationUpdate, db: Session = Depends(get_db)):
    updated = crud.update_destination(db, destination_id, destination)
    if not updated:
        raise HTTPException(status_code=404, detail="Destination not found")
    return updated


@router.delete("/{destination_id}")
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_destination(db, destination_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Destination not found")
    return {"ok": True, "message": "Destination deleted"}