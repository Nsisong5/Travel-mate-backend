from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy.dialects.postgresql import JSONB
from typing import List

class Etinerary(Base):
    __tablename__ = "etineraries"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String, nullable=False)
    title = Column(String, nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    items = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)    
    #relationships
    trip = relationship("Trip", back_populates="etineraries")
    
    

