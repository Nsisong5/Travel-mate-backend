
import itineraries
import logging
from fastapi.staticfiles import StaticFiles
from api.routes import router as api_routes
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date
from database import Base, engine, get_db
import models, schemas
import Models.budget
from Models.destination import Destination 
import Models.YearlyBudget
from auth.auth import router as auth_router, verify_password, hash_password as get_password_hash
from deps import get_current_user
from budget.routes import router as budget_routes
from users.avatar import router as uploads
from users.ai_recommendation import router as rcmdt_router
from utils.get_trip_duration import calculate_duration
from users.avatar import router as avatar_router # Import your avatar router
from users.active_ai_recommendations import router as active_router
from routers.budget import router as budget_router
from routers.YearlyBudget import router as y_router
from routers.destination  import router as destination_router
from routers.etinerary import router as etinerary_router
from Models.etinerary import Etinerary
from AIService.travel_tips_endpoints import router as travel_tips_router
from AIService.recommendations_control import router as c_router
from AIService import AIService
from AIService.endpoints import router as ai_service_router

import json
import os




Base.metadata.create_all(bind=engine)

app = FastAPI(title="TravelMate API")


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(travel_tips_router)
app.include_router(c_router)
app.include_router(ai_service_router)
app.include_router(y_router)
app.include_router(destination_router)
app.include_router(budget_router)
app.include_router(active_router)
app.include_router(itineraries.router)
app.include_router(api_routes, prefix="/api")
app.include_router(auth_router)
app.include_router(budget_routes)
app.include_router(uploads)
app.include_router(rcmdt_router, prefix="/user")
app.include_router(avatar_router, tags=["avatars"])
app.include_router(etinerary_router)







app.mount(
    "/static/avatars", 
    StaticFiles(directory="uploads/avatars"), 
    name="avatars"
)



@app.on_event("startup")
async def create_upload_directories():
    os.makedirs("uploads/avatars", exist_ok=True)
   


@app.patch("/user/profile", response_model=schemas.UserOut)
def patch_profile_extended(
    payload: schemas.ProfilePatch, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)

):
    """Update user profile with comprehensive field support"""
    
    # Update basic profile fields
    if payload.full_name is not None:
        user.full_name = payload.full_name
        
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    
  
    if payload.phone is not None:
        user.phone = payload.phone
        
    if payload.bio is not None:
        user.bio = payload.bio
        
    if payload.country is not None:
        user.country = payload.country
    
    if payload.email is not None:
        # Check if email is already taken
        existing_user = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.id != user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="Email already registered"
            )
        user.email = payload.email
    
    # Handle password update
    if payload.new_password is not None:
        if payload.current_password is None:
            raise HTTPException(
                status_code=400, 
                detail="Current password required to set new password"
            )
        
        # Verify current password
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(
                status_code=400, 
                detail="Current password is incorrect"
            )
        
        # Hash and set new password
        user.hashed_password = get_password_hash(payload.new_password)
    
    # Commit changes
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update profile")
    
    return user



@app.get("/AITest")
def get_profile():
    user_data_format = {
    "past_trips": [  # List of user's previous trips
        {
            "destination": "Paris, France",      # Required: Full destination name
            "type": "leisure",                   # Optional: trip type
            "duration": 5,                       # Optional: days
            "budget": 120,                       # Optional: daily budget
            "rating": 4.5,                       # Optional: user's rating of trip
            "year": 2023,                        # Optional: when they traveled
            "activities": ["museums", "food"]     # Optional: what they did
        },
        {
            "destination": "Tokyo, Japan",
            "type": "cultural", 
            "duration": 7,
            "budget": 150,
            "rating": 5.0,
            "year": 2023,
            "activities": ["temples", "shopping", "food"]
        },
        
    ],
    
    "preferences": {  
        "lifestyle": "balanced",             
        "travel_style": "moderate",    
        "group_type": "solo",                
        "activities": "museums, food, nature", 
        "interests": "history, culture, art",
        "accommodation": "mid-range",     
        "food_preference": "local",           
        "pace": "relaxed",                    
        "budget_range": "moderate"          
    }
   }
    response = ai_service.get_destination_recommendations(user_data_format)
    return response



@app.get("/custom-error/")
async def custom_error():
    raise HTTPException(status_code=400, detail="Invalid Request", headers={"X-Error": "CustomHeader"})
    
@app.get("/user/profile", response_model=schemas.UserOut)
def get_profile(user: models.User = Depends(get_current_user)):
    return user




@app.get("/trips/history", response_model=list[schemas.TripOut])
def trips_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    trips = db.query(models.Trip).filter(models.Trip.user_id == user.id, models.Trip.status == models.TripStatus.completed).all()
    return trips
    
@app.get("/trips", response_model=list[schemas.TripOut])
def trips_history(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    trips = db.query(models.Trip).filter(models.Trip.user_id == user.id).all()
    return trips





@app.get("/trips/upcoming", response_model=list[schemas.TripOut])
def trips_upcoming(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    trips = db.query(models.Trip).filter(models.Trip.user_id == user.id, models.Trip.status.in_([models.TripStatus.planned, models.TripStatus.planned])).all()
    return trips




@app.patch("/trips/{trip_id}", response_model=schemas.TripOut)
def update_trip(trip_id: str, updates: schemas.TripCreate, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="trip not found")
    
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(trip, key, value)
    
    db.commit()
    db.refresh(trip)
    return trip




@app.get("/trips/{id}", response_model=schemas.TripOut)
def trips_upcoming(
    id: int,
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.id == id).first()
    return trip



@app.post("/trips", response_model=schemas.TripOut)
def create_trip(
    payload: schemas.TripCreate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    print(f"Creating trip for user: {user.email}")
    print(f"Payload received: {payload.dict()}")
    
    try:
        # Calculate duration
        duration = calculate_duration(payload.start_date, payload.end_date)
        
        # Create trip object
        trip = models.Trip(
            user_id=user.id,
            destination=payload.destination,
            start_date=payload.start_date,
            end_date=payload.end_date,
            style=payload.style,
            has_budget=payload.has_budget,
            duration=duration,
            status=payload.status,  # Enum will be handled automatically
            budget_range=payload.budget_range,
            origin = payload.origin,
            cost_estimated = payload.cost_estimated or True,
            state = payload.state or None,
            country = payload.country or None,
            local_gov = payload.local_gov or None,
            title = payload.title or None,
            travelers= payload.travelers or 1
               # Enum will be handled automatically
        )
        db.add(trip)
        db.flush()
               
        
        itinerary  = Etinerary(
        title = "Arrival",
        day = "1",
        trip_id = trip.id,
        items = json.dumps([]))
      
        db.add(itinerary)  

        db.commit()
        db.refresh(trip)
        db.refresh(trip)
        
        print(f"Itinerary saved successfully with ID: {itinerary.id}")
        return trip
        
    except Exception as e:
        print(f"Error creating trip: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")


@app.delete("/trips/{id}", response_model=schemas.Message)
def trip_delete(
   id: int,
   db: Session= Depends(get_db),
   user: models.User= Depends(get_current_user)):
   
   try:
       trip = db.query(models.Trip).filter(
          models.Trip.id == id
       ).first()
       if not trip:
            raise HTTPException(status_code=404, detail={"message": "trip not found"})
       db.delete(trip)
       db.commit()
       return {"message": "trip successfully deleted" }
   except Exception as e:
        raise
   except HTTPException as e:
         db.rollback()
         raise HTTPException(status_code=500, detail={"Error: ",e})
  
@app.post("/trips/test")
def test_trip_endpoint(user: models.User = Depends(get_current_user)):
    return {"message": "Trip endpoint accessible", "user": user.email}


@app.get("/places/saved", response_model=list[schemas.SavedPlaceOut])
def saved_places(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.SavedPlace).filter(models.SavedPlace.user_id == user.id).all()





@app.delete("/places/{rec_id}", response_model=schemas.Message)
def delete(
     rec_id: int,
     db: Session = Depends(get_db), 
     user: models.User = Depends(get_current_user)):
    try:  
        saveplace_map = db.query(models.SavedPlace).filter(
           models.SavedPlace.rec_id == rec_id
           ).first()           
        
        if not saveplace_map:
            raise HTTPException(
                status_code=404, 
                detail="SavePlaceMap not found or not accessible"
            )
        db.delete(saveplace_map)
        db.commit()
        print(f"Saveplace deleted successfully")
        return {"message": "Saveplace deleted successfully"}
        
            
    except HTTPException:
       raise 
    except Exception as e:
        print(f"Error deleting Saveplace map: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed deleting Saveplace map: {str(e)}")

@app.post("/places", response_model=schemas.SavedPlaceOut)
def add_saved_plac(payload: schemas.SavedPlaceCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sp = models.SavedPlace(
     user_id=user.id,
     rec_id = payload.rec_id)
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp

@app.get("/recommendations")
def recommendations(user: models.User = Depends(get_current_user)):
    # Simple, fast mock from server (swap later for real AI service)
    return {
        "items": [
            {"id": 1, "name": "Bali", "description": "Tropical paradise with sunsets"},
            {"id": 2, "name": "Reykjavik", "description": "Northern lights & volcanic landscapes"},
            {"id": 3, "name": "Lisbon", "description": "Historic city with coastal charm"},
        ]
    }

#
    
    

