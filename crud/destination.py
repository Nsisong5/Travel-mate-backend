from sqlalchemy.orm import Session
import Models.destination as models
import Schemas.destination as schemas 


def create_destination(db: Session, destination: schemas.DestinationCreate):
    
    db_destination = models.Destination(
        name=destination.name,
        country=destination.country,
        country_code=destination.countryCode,
        category=destination.category,
        budget=destination.budget,
        image_url=destination.imageUrl,
        description=destination.description,
        user_id=destination.user_id,
    )
    db.add(db_destination)
    db.commit()
    db.refresh(db_destination)
    return db_destination


def get_destinations(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Destination).offset(skip).limit(limit).all()


def get_destination_by_id(db: Session, destination_id: int):
    return db.query(models.Destination).filter(models.Destination.id == destination_id).first()


def update_destination(db: Session, destination_id: int, destination: schemas.DestinationUpdate):
    db_destination = db.query(models.Destination).filter(models.Destination.id == destination_id).first()
    if not db_destination:
        return None

    for key, value in destination.dict(exclude_unset=True).items():
        setattr(db_destination, key if key != "countryCode" else "country_code", value)

    db.commit()
    db.refresh(db_destination)
    return db_destination


def delete_destination(db: Session, destination_id: int):
    db_destination = db.query(models.Destination).filter(models.Destination.id == destination_id).first()
    if db_destination:
        db.delete(db_destination)
        db.commit()
    return db_destination