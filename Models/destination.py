from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    country_code = Column(String(5), nullable=False)
    category = Column(String(50), nullable=False)
    budget = Column(String(50), nullable=False)
    image_url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    #users = relationship("UserDestination", back_populates="destination")