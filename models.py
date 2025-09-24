from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, Float, Enum, ForeignKey,func,JSON,Text
from sqlalchemy.orm import relationship
from Models.YearlyBudget import YearlyBudget
from database import Base
import enum
from sqlalchemy.types import DateTime, Date, Time







class TransportType(enum.Enum):
    plane = "plane"
    active = "bus"
    car = "car"
    motorcycle = "motorcycle"

class TripStatus(enum.Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class BudgetRange(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    luxury = "luxury"
   
 

#class UserDestination(Base):
#    __tablename__ = "user_destinations"
#    
#    # Primary key for the association table itself
#    id = Column(Integer, primary_key=True)
#    
#    # Foreign key linking to the users table
#    user_id = Column(Integer, ForeignKey("users.id"))
#    
#    # Foreign key linking to the destinations table
#    destination_id = Column(Integer, ForeignKey("destinations.id"))

#    def __repr__(self):
#        return f"<UserDestination(user_id={self.user_id}, destination_id={self.destination_id})>"
#                
#                      

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    avatar_url = Column(String, default="")
    budgets = relationship("Budget", back_populates="user")   
    phone =  Column(String, default=None ,nullable=True)
    bio =  Column(String, default="", nullable=True)
    country = Column(String, default="", nullable=True) 
    created_at = Column(DateTime(timezone=True),server_default=(func.now())) 
    #destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=True)
    
#    state = Column(String, default="", nullable=True)
#    location = Column(String, default="", nullable=True)
#    local_gov = Column(String, default="", nullable=True)
#    
    trips = relationship("Trip", back_populates="owner", cascade="all, delete")     
    saved_places = relationship("SavedPlace", back_populates="owner", cascade="all, delete")    
    #destinations = relationship("UserDestination", back_populates="user")   
    yearly_budget = relationship("YearlyBudget", back_populates="user")
    recommendations = relationship("AIRecommendation", back_populates="user")    
    active_ai_recommendations = relationship(
        "ActiveTripAIRecommendation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def get_avatar_url(self, base_url: str = "") -> str:
        """Helper method to get full avatar URL"""
        if not self.avatar_url:
            return ""
        
        # If it's already a full URL (cloud storage), return as is
        if self.avatar_url.startswith(('http://', 'https://')):
            return self.avatar_url
        
        # If it's a relative path (local storage), prepend base URL
        if self.avatar_url.startswith('/uploads/'):
            return f"{base_url.rstrip('/')}{self.avatar_url}"
        
        return self.avatar_url

    def has_avatar(self) -> bool:
        """Check if user has an avatar"""
        return bool(self.avatar_url and self.avatar_url.strip())

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"
    
       




class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    style = Column(String, nullable=False)
    duration = Column(String, nullable=True)  # Will be calculated
    cost = Column(Float, default=0.0, nullable=True)
    origin = Column(String,nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.planned)
    budget_range = Column(Enum(BudgetRange), default=BudgetRange.medium)
    created_at = Column(DateTime(timezone=True),server_default=(func.now()))
    means = Column(String, nullable=True, default="car")
    cost_estimated = Column(Boolean, default=True,nullable=False)
    rating = Column(Integer, default=0, nullable=True)
    itineraries = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan")
    budget = relationship("Budget",back_populates="trip", cascade="all, delete-orphan")
    state = Column(String, default="", nullable=True)
    local_gov = Column(String, default="", nullable=True)
    country = Column(String, default="", nullable=True)
    has_budget = Column(Boolean, server_default="false", nullable=True)
    title = Column(String, nullable=True)
    travelers = Column(Integer, nullable=True)
    # Relationship
    owner = relationship("User", back_populates="trips")
    etineraries = relationship("Etinerary",back_populates="trip")
    active_ai_recommendations = relationship(
        "ActiveTripAIRecommendation",
         back_populates="trip",
         cascade="all, delete-orphan"
       )


class SavedPlace(Base):
    __tablename__ = "saved_places"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    rec_id = Column(Integer, nullable=False, index=True)
    owner = relationship("User", back_populates="saved_places")
    
    



class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    category = Column(String(50),index=True)
    budget_category =  Column(String(50), index=True)
    lifestyle_category =  Column(String(50), index=True, nullable=True)
    location = Column(String(100), index=True) 
    
    name = Column(String(50), index=True) 
    settlement_type =  Column(String(50), index=True, default="city", nullable=True)  
    destination_type = Column(String(50), index=True)         # e.g. "Destinations", "Hotels", "Activities", "Tips"
    title = Column(String(255), nullable=False)   # e.g. "Paris, France"
    description = Column(String(1000), nullable=True)
    image = Column(String(500), nullable=True)    # Image URL
    image2 = Column(String(500), nullable=True)    # Image URL    
    image3 = Column(String(500), nullable=True)    # Image URL
    image4 = Column(String(500), nullable=True)    # Image URL    
    tags = Column(JSON, nullable=True)            # Array of tags (["Luxury", "Popular"])
    
    estimated_cost = Column(Integer, nullable=True, default=0)
    popularity = Column(Integer, default=0, index=True)   # could track number of views/saves
    rating = Column(Float, default=0.0, index=True)       # average rating 1–5
    budget_score = Column(Integer, default=0, index=True) # relative "budget-friendly" score

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="recommendations")
    
    




class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"))
    day = Column(Integer)
    title = Column(String)

    trip = relationship("Trip", back_populates="itineraries")
    activities = relationship("Activity", back_populates="itinerary", cascade="all, delete-orphan")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id", ondelete="CASCADE"))
    name = Column(String)
    location = Column(String, nullable=True)
    time = Column(String, nullable=True)

    itinerary = relationship("Itinerary", back_populates="activities")    
    
        

class ActiveTripAIRecommendation(Base):
    __tablename__ = "active_trip_ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    # Associate to user who requested or owns the recommendation (optional but useful)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Optionally associate to a Trip (if this rec is tied to an active trip)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True, index=True)

    # Basic identity / meta
    rec_id = Column(String(100), unique=True, nullable=True, index=True)  # e.g. "rec-123" from AI
    title = Column(String(255), nullable=False, index=True)
    destination = Column(String(200), nullable=True, index=True)
    category = Column(String(80), nullable=True, index=True)  # Dining, Activities, Tips etc.

    # Rich content
    cover_image = Column(String(500), nullable=True)
    images = Column(JSON, nullable=True)           # JSON array of image urls
    description = Column(Text, nullable=True)
    cultural_tips = Column(JSON, nullable=True)   # JSON array of strings
    location = Column(JSON, nullable=True)        # { name, coordinates: {lat, lng} }

    # Info fields
    best_time = Column(String(80), nullable=True)
    estimated_cost = Column(String(80), nullable=True)
    popularity = Column(Integer, default=0, index=True)
    rating = Column(Float, default=0.0)
    in_itinerary = Column(Integer, default=0)  # 0/1 integer to keep it DB simple

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (adjust "back_populates" if names differ)
    user = relationship("User", back_populates="active_ai_recommendations", foreign_keys=[user_id])
    trip = relationship("Trip", back_populates="active_ai_recommendations", foreign_keys=[trip_id])            
                    