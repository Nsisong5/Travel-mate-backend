
from pydantic import BaseModel, validator,EmailStr,Field
from typing import Optional,List,Dict, Any
from datetime import date
from enum import Enum
from datetime import datetime

from datetime import datetime




class Message(BaseModel):
    message: str



class TripStatus(str, Enum):
    planned = "Planned"
    upcoming = "Upcoming"
    completed = "Completed"





class BudgetBase(BaseModel):
    amount: float
    period: str
    purpose: str | None = None

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    created_at: Optional[int] =None

    class Config:
        orm_mode = True




class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = ""

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = ""
    phone: Optional[str] = None
    bio: Optional[str] = ""
    country: Optional[str]  = ""
    created_at: Optional[datetime] = "" 
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# schemas.py - Complete Trip Schemas


# Enums that match your model
class TripStatusEnum(str, Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class BudgetRangeEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    luxury = "luxury"

class TripCreate(BaseModel):
    """Schema for creating a trip"""
    destination: str
    start_date: date
    end_date: date
    status: TripStatusEnum
    budget_range: BudgetRangeEnum  # Changed from 'budget' to match model
    style: str
    origin: str 
    means : str
    cost_estimated: bool = ...
    has_budget: Optional[bool] = False 
    rating: Optional[int] = 0
    travelers: Optional[int] = 1
    local_gov: Optional[str] = ""
    country:Optional[str] = ""
    state:  Optional[str] = ""
    title : Optional[str] = ""
    @validator('destination')
    def validate_destination(cls, v):
        if not v or not v.strip():
            raise ValueError('Destination cannot be empty')
        return v.strip()
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class TripOut(BaseModel):
    """Schema for trip output"""
    id: int
    user_id: int
    destination: str
    start_date: date
    end_date: date
    city: Optional[str] = ""
    style: str
    duration: Optional[str] = None
    cost: Optional[float] = None
    status: str
    budget_range: str
    origin: str
    means: str
    cost_estimated: bool
    created_at: datetime 
    rating: Optional[int] = 0
    country: str
    has_budget: Optional[bool] = False
    title : Optional[str] = ""
    state : Optional[str] = ""
    local_gov : Optional[str] = ""
    travelers : Optional[int] = 1
    
    class Config:
        from_attributes = True
        
        

class SavedPlaceBase(BaseModel):
    rec_id: int
    user_id: int


class SavedPlaceCreate(SavedPlaceBase):
    user_id: Optional[int] = None

class SavedPlaceOut(SavedPlaceBase):
    id: int
    user_id: int
    rec_id: int
    class Config:
        orm_mode = True

class ProfilePatch(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    email: Optional[EmailStr] = None  # Allow email updates
    current_password: Optional[str] = None  # Required for password change
    new_password: Optional[str] = None    
 
   
   


# schemas.py - AI Recommendation Schemas




# schemas.py - AI Recommendation Schemas


class AIRecommendationCreate(BaseModel):
    """Schema for creating an AI recommendation""" 
    category: str
    location: str
    name: str
    destination_type: str  # "Destinations", "Hotels", "Activities", "Tips"
    title: str
    budget_category: Optional[str] = "Medium"
    lifestyle_category: Optional[str] = "Adventure"
    settlement_type: Optional[str] = ""
    description: Optional[str] = None
    image: Optional[str] = None
    image2: Optional[str] = None
    image3: Optional[str] = None
    image4: Optional[str] = None
    tags: Optional[List[str]] = None
    popularity: Optional[int] = 0
    rating: Optional[float] = 0.0
    budget_score: Optional[int] = 0
    
    @validator('category')
    def validate_category(cls, v):
        if not v or not v.strip():
            raise ValueError('Category cannot be empty')
        return v.strip()
    
    @validator('location')
    def validate_location(cls, v):
        if not v or not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('destination_type')
    def validate_type(cls, v):
        allowed_types = ["Destinations", "Hotels", "Activities", "Tips"]
        if v not in allowed_types:
            raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('Rating must be between 0 and 5')
        return v
    
    @validator('popularity')
    def validate_popularity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Popularity cannot be negative')
        return v
    
    @validator('budget_score')
    def validate_budget_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Budget score must be between 0 and 100')
        return v

class AIRecommendationUpdate(BaseModel):
    """Schema for updating an AI recommendation"""
    destination_type : Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None
    destination_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None
    popularity: Optional[int] = None
    rating: Optional[float] = None
    budget_score: Optional[int] = None
    
    @validator('destination_type')
    def validate_type(cls, v):
        if v is not None:
            allowed_types = ["Destinations", "Hotels", "Activities", "Tips"]
            if v not in allowed_types:
                raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('Rating must be between 0 and 5')
        return v

class AIRecommendationOut(BaseModel):
    """Schema for AI recommendation output"""
    category: str
    id: int
    user_id: int
    destination_type: str
    lifestyle_category: str
    budget_category:Optional[str] = None
    location: str
    name: str
    destination_type: str
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    imag2: Optional[str] = None
    imag3: Optional[str] = None
    imag4: Optional[str] = None
    tags: Optional[List[str]] = None
    popularity: int
    rating: float
    budget_score: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIRecommendationFilter(BaseModel):
    """Schema for filtering recommendations"""
    category: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    min_rating: Optional[float] = None
    max_budget_score: Optional[int] = None
    tags: Optional[List[str]] = None
    limit: Optional[int] = 10
    offset: Optional[int] = 0 
    

class ActivityBase(BaseModel):
    name: str
    location: Optional[str] = None
    time: Optional[str] = None


class ActivityCreate(ActivityBase):
    pass


class Activity(ActivityBase):
    id: int
    itinerary_id: int

    class Config:
        orm_mode = True


class ItineraryBase(BaseModel):
    day: int
    title: str


class ItineraryCreate(ItineraryBase):
    pass


class Itinerary(ItineraryBase):
    id: int
    trip_id: int
    activities: List[Activity] = []

    class Config:
        orm_mode = True                                        


# schemas/ai_schemas.py

class LocationSchema(BaseModel):
    name: Optional[str]
    coordinates: Optional[dict] = None  # { lat: float, lng: float }

class ActiveAIRecommendationBase(BaseModel):
    rec_id: Optional[str]
    title: str
    destination: Optional[str]
    category: Optional[str]
    cover_image: Optional[str]
    images: Optional[List[str]] = []
    description: Optional[str] = None
    cultural_tips: Optional[List[str]] = []
    tags: Optional[List[str]] = None
    location: Optional[LocationSchema] = None
    best_time: Optional[str] = None
    estimated_cost: Optional[str] = None
    popularity: Optional[int] = 0
    rating: Optional[float] = 0.0
    in_itinerary: Optional[bool] = False
    
        
class ActiveAIRecommendationCreate(ActiveAIRecommendationBase):
    # trip_id and user_id are handled server-side via get_current_user or route args
    trip_id: Optional[int] = None

class ActiveAIRecommendationUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    in_itinerary: Optional[bool]
    rating: Optional[float]

class ActiveAIRecommendationOut(ActiveAIRecommendationBase):
    id: int
    user_id: Optional[int]
    trip_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True  
        
                                                                                                                                                                                                                                                                                                                  


class FormattedTravelTips(BaseModel):
    culture_customs: List[str]
    culture_etiquette: List[str]
    culture_dress_code: str
    language_basic_phrases: List[str]
    language_tips: str
    practical_currency: str
    practical_tipping: str
    practical_transportation: str
    practical_safety: List[str]

    class Config:
        # Pydantic v1 required this for compatibility with SQLAlchemy
        orm_mode = True # Use 'from_attributes = True' in Pydantic v2


class TravelTipsCreate(BaseModel):
    trip_id: int = Field(..., description="The ID of the trip this tips data belongs to.")
    raw_tips_data: Dict[str, Any] = Field(..., description="The raw nested JSON data from the AI service.")



class TravelTipsResponse(BaseModel):    
    id: int
    trip_id: int
    # Use FormattedTravelTips schema for the tips content
    tips_content: "FormattedTravelTips"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     ''                                                                                                                                                                                                                                                                                                          