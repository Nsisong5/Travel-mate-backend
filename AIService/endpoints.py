# api/travel_endpoints.py

from fastapi import APIRouter, HTTPException, Depends 
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime
from deps import get_current_user
from sqlalchemy.orm import Session
from database import get_db
from AIService.utils import save_travel_tips_to_db
import models
import schemas


from AIService.AIService import ai_service 
from AIService.image_service import ImageService
# Setup
router = APIRouter(prefix="/api/travel-recs", tags=["Travel AI"])
logger = logging.getLogger(__name__)

image_service = ImageService()


# ========== REQUEST MODELS ==========
class DestinationRequest(BaseModel):
    user_id: int
    budget: Optional[float] = 100.0
    trip_type: str = "leisure"

class CurrentTripRequest(BaseModel):
    id: int
    destination: str
    country: str
    trip_type: str = "leisure" 
    duration: str

class TravelTipsRequest(BaseModel):
    trip_id: int
    destination: str
    country: str
    season: str = "current"

# ========== MOCK DATA ==========


MOCK_USER_DATA = {
    1: {
        "past_trips": [
            {
                "destination": "Paris, France",
                "type": "cultural",
                "duration": 6,
                "budget": 120,
                "rating": 4.5,
                "activities": ["museums", "cafes", "architecture"]
            },
            {
                "destination": "Tokyo, Japan", 
                "type": "adventure",
                "duration": 8,
                "budget": 150,
                "rating": 5.0,
                "activities": ["temples", "food tours", "shopping"]
            },
            {
                "destination": "Barcelona, Spain",
                "type": "leisure",
                "duration": 5,
                "budget": 90,
                "rating": 4.2,
                "activities": ["beaches", "tapas", "gaudi buildings"]
            }
        ],
        "preferences": {
            "lifestyle": "balanced",
            "travel_style": "moderate",
            "group_type": "solo",
            "activities": "museums, local food, photography",
            "interests": "art, history, local cuisine, architecture"
        }
    },
    
    2: {
        "user_id":1,
        "past_trips": [
            {
                "destination": "Bali, Indonesia",
                "type": "leisure", 
                "duration": 12,
                "budget": 60,
                "rating": 4.8,
                "activities": ["beaches", "yoga", "temples"]
            },
            {
                "destination": "Bangkok, Thailand",
                "type": "adventure",
                "duration": 7,
                "budget": 45,
                "rating": 4.3,
                "activities": ["street food", "markets", "temples"]
            },
            {
                "destination": "Ho Chi Minh City, Vietnam",
                "type": "cultural",
                "duration": 6,
                "budget": 40,
                "rating": 4.6,
                "activities": ["food tours", "history museums", "motorbike tours"]
            }
        ],
        "preferences": {
            "lifestyle": "budget",
            "travel_style": "slow",
            "group_type": "couple", 
            "activities": "street food, beaches, local culture",
            "interests": "budget travel, authentic experiences, nature"
        }
    },
    
    3: {
        "past_trips": [
            {
                "destination": "Dubai, UAE",
                "type": "luxury",
                "duration": 4,
                "budget": 300,
                "rating": 4.7,
                "activities": ["luxury shopping", "fine dining", "spa"]
            },
            {
                "destination": "Santorini, Greece",
                "type": "romantic",
                "duration": 6,
                "budget": 250,
                "rating": 5.0,
                "activities": ["sunset viewing", "wine tasting", "luxury resorts"]
            }
        ],
        "preferences": {
            "lifestyle": "luxury",
            "travel_style": "relaxed",
            "group_type": "couple",
            "activities": "fine dining, luxury experiences, spas",
            "interests": "luxury travel, comfort, exclusive experiences"
        }
    },
    
    4: {
        "past_trips": [], # New traveler
        "preferences": {
            "lifestyle": "balanced",
            "travel_style": "moderate", 
            "group_type": "family",
            "activities": "family-friendly attractions, safe destinations",
            "interests": "family travel, kid-friendly activities"
        }
    }
}

def get_mock_user_data(user_id: int) -> Dict:
    """Get mock user data for testing"""
    return MOCK_USER_DATA.get(user_id, MOCK_USER_DATA[4])  # Default to new traveler

# ========== ENDPOINTS ==========

@router.get("/mock-users")
async def get_available_mock_users():
    """See available mock users for testing"""
    
    user_summaries = {}
    for user_id, data in MOCK_USER_DATA.items():
        past_trips = data["past_trips"]
        preferences = data["preferences"]
        
        user_summaries[user_id] = {
            "description": f"User {user_id}",
            "past_trips_count": len(past_trips),
            "destinations_visited": [trip["destination"] for trip in past_trips],
            "travel_style": preferences.get("lifestyle", "balanced"),
            "typical_budget": past_trips[0]["budget"] if past_trips else "None",
            "interests": preferences.get("interests", "General")
        }
    
    return {
        "available_users": user_summaries,
        "usage": "Use user_id 1-4 in your API calls to test different traveler profiles"
    }

@router.get("/mock-users/{user_id}")
async def get_mock_user_details(user_id: int):
    """Get detailed mock data for a specific user"""
    
    if user_id not in MOCK_USER_DATA:
        raise HTTPException(status_code=404, detail="User not found. Use user_id 1-4")
    
    mock_data = get_mock_user_data(user_id)
    
    return {
        "user_id": user_id,
        "mock_data": mock_data,
        "summary": {
            "total_past_trips": len(mock_data["past_trips"]),
            "average_budget": sum(trip.get("budget", 0) for trip in mock_data["past_trips"]) / max(len(mock_data["past_trips"]), 1),
            "preferred_trip_types": list(set(trip.get("type", "") for trip in mock_data["past_trips"])),
            "lifestyle": mock_data["preferences"]["lifestyle"]
        }
    }

@router.post("/destinations")
async def get_destination_recommendations(request: DestinationRequest):
    """
    Get AI destination recommendations using mock user data
    
    Test with:
    - user_id: 1 (cultural traveler), 2 (budget backpacker), 3 (luxury), 4 (new traveler)
    - budget: 50-500 (daily USD)
    - trip_type: leisure, adventure, cultural, romantic, business
    """
   
    start_time = datetime.now()
    
    try:
        # Get mock user data
        user_data = get_mock_user_data(request.user_id)
        
        logger.info(f"Getting destination recommendations for user {request.user_id}")
        logger.info(f"User has {len(user_data['past_trips'])} past trips")
        
        # Call your AI service
        
        recommendations = await ai_service.get_destination_recommendations(
            user_data=user_data,
            budget=request.budget,
            trip_type=request.trip_type
        )
     
              
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "user_id": request.user_id,
            "input_parameters": {
                "budget": request.budget,
                "trip_type": request.trip_type
            },
            "user_profile_summary": {
                "past_destinations": [trip["destination"] for trip in user_data["past_trips"]],
                "lifestyle": user_data["preferences"]["lifestyle"],
                "interests": user_data["preferences"]["interests"]
            },
            "recommendations": recommendations,
            "count": len(recommendations),
            "processing_time_seconds": round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting destination recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.post("/current-trip")
async def get_current_trip_recommendations(
   request: CurrentTripRequest,
   db: Session = Depends(get_db),
   user = Depends(get_current_user)):
    
    """
    Get AI recommendations for current trip activities
    
    Test with different destinations:
    - "Paris, France", "Tokyo, Japan", "Bangkok, Thailand"
    - "New York, USA", "London, UK", "Barcelona, Spain"
    """
    
    start_time = datetime.now()
    
    try:
        logger.info(f"Getting current trip recommendations for {request.destination}")
        
       
        recommendations = await ai_service.get_current_trip_recommendations(
            destination=request.destination,
            country = request.country,
            trip_type=request.trip_type,
            duration=request.duration
        )
     
        for recommendation in  recommendations:
             print(recommendation)
             print()  
             db_recommendation = models.ActiveTripAIRecommendation(          
        title=recommendation.get("title"),
        destination=recommendation.get("destination"),
        category=recommendation.get("category"),
        cover_image=recommendation.get("coverImage"),
        images=recommendation.get("images") or [],
        description=recommendation.get("description"),
        cultural_tips=recommendation.get("culturalTips") or [],
        location = recommendation.get("location") if recommendation.get("location") else None,
        best_time=recommendation.get("bestTime"),
        estimated_cost=recommendation.get("estimatedCost"),
        popularity=recommendation.get("popularity") or 0,
        rating=recommendation.get("rating") or 0.0,
        tags= recommendation.get("tags"),
        in_itinerary=1 if recommendation.get("inItinerary") else 0,
        user_id=user.id,
        trip_id=request.id    
             )
             db.add(db_recommendation)
             db.commit()
             db.refresh(db_recommendation)
        processing_time = (datetime.now() - start_time).total_seconds()                                 
        return {
            "success": True,
            "destination": request.destination,
            "input_parameters": {
                "trip_type": request.trip_type,
                "duration": request.duration
            },
            "recommendations": recommendations,
            "count": len(recommendations),
            "categories": list(set(rec.get("category", "") for rec in recommendations)),
            "processing_time_seconds": round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting current trip recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@router.post("/travel-tips")
async def get_travel_tips(
 request: TravelTipsRequest,
  db: Session = Depends(get_db) 
 
):
    """
    Get AI travel tips for a destination
    
    Test with:
    - destination: "Tokyo, Japan", "Paris, France", "Bangkok, Thailand"
    - season: "spring", "summer", "fall", "winter", "current"
    """
    
    start_time = datetime.now()

    try:
        logger.info(f"Getting travel tips for {request.destination} in {request.season}")
        
        # Call your AI service
        tips = await ai_service.get_travel_tips(
            destination=request.destination,
            country=request.country,
            season=request.season
            
        )                
        processing_time = (datetime.now() - start_time).total_seconds()
        save_data = save_travel_tips_to_db(db, request.trip_id,tips)        
        print("travel tips data save to database:",save_data)
        return save_data
    except Exception as e:
        logger.error(f"Error getting travel tips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get travel tips: {str(e)}")

@router.get("/test-ai-connection")
async def test_ai_connection():
    """Test if AI service is working"""
    
    try:
        # Test with minimal data
        test_user_data = {
            "past_trips": [{"destination": "Paris, France", "type": "leisure"}],
            "preferences": {"lifestyle": "balanced"}
        }
        
        # Quick test call
        recommendations = await ai_service.get_destination_recommendations(
            user_data=test_user_data,
            budget=100.0,
            trip_type="leisure"
        )
        
        return {
            "ai_service_status": "working",
            "test_call_successful": True,
            "sample_recommendations_count": len(recommendations),
            "sample_recommendation": recommendations[0] if recommendations else None
        }
        
    except Exception as e:
        return {
            "ai_service_status": "error",
            "error": str(e),
            "test_call_successful": False
        }


#======== images endpoints =========

@router.get("/test/images")
async def test_images():
    """Test image service independently"""
    
  # Test with mock destinations
    destinations = [
        {"name": "Paris", "location": "France", "title": "Paris, France", "settlement_type": "city"},
        {"name": "Tokyo", "location": "Japan", "title": "Tokyo, Japan", "settlement_type": "city"}
    ]
    
    
    enhanced = await image_service.enhance_destinations_with_images(destinations, 4)
    
    return {
        "test": "successful",
        "destinations_processed": len(enhanced),
        "sample_images": {
            "destination": enhanced[0]["title"],
            "image1": enhanced[0].get("image"),
            "image2": enhanced[0].get("image2"),
            "total_images": sum(1 for img in [enhanced[0].get(f"image{i}") for i in ['', '2', '3', '4']] if img)
        }
    }
    
    
    



@router.post("/ai_rec_detail/{rec_id}", response_model=schemas.ActiveAIRecommendationOut)
async def get_current_trip_recommendations_detail(
   rec_id: int,
   db: Session = Depends(get_db),
   user = Depends(get_current_user)):
   
   try:
        rec = db.query(models.ActiveTripAIRecommendation.id == rec_id).first()
        return rec
   except Exception as e:
       raise HTTPException(status_code=500, detail=f"fail to fetch recommendation: {e}")
       
       
        