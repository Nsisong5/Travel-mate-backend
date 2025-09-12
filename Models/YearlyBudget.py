from sqlalchemy import Column, Integer, String, Float,ForeignKey
from sqlalchemy.orm import relationship

from database import Base

class YearlyBudget(Base):
    """
    SQLAlchemy model for the yearly_budget table.
    """
    __tablename__ = "yearly_budget"

    id = Column(Integer, primary_key=True, index=True)
    total = Column(Float, nullable=False)
    used = Column(Float, nullable=False)
    year = Column(Integer, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Define a relationship with the TripBudget model.
    # The 'back_populates' ensures a two-way relationship.
    # We assume 'TripBudget' has a 'yearly_budget_id' foreign key.
    # This line is for demonstration of the relationship; the TripBudget model itself isn't defined here.
    budget = relationship("Budget", back_populates="yearly_budget")
        
    user = relationship("User", back_populates="yearly_budget")

# Note: As you mentioned, the TripBudget model has already been taken care of.
# A hypothetical TripBudget model would look something like this to establish the relationship:
# from sqlalchemy import ForeignKey
# class TripBudget(Base):
    ...
#    yearly_budget_id = Column(Integer, ForeignKey("yearly_budget.id"))
#    yearly_budget = relationship("YearlyBudget", back_populates="trips")
