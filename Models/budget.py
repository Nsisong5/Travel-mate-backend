# models/
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    trip_id = Column(Integer, ForeignKey("trips.id"))
    amount = Column(Float, nullable=False)
    period = Column(String, nullable=False, default="trip")  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    yearly_budget_id = Column(Integer, ForeignKey("yearly_budget.id"))
    
    # relationships
    allocations = relationship("BudgetAllocation", back_populates="budget", cascade="all, delete")
    expenses = relationship("Expense", back_populates="budget", cascade="all, delete")
    trip = relationship("Trip", back_populates="budget")
    user = relationship("User", back_populates="budgets")    
    yearly_budget = relationship("YearlyBudget", back_populates="budget")


class BudgetAllocation(Base):
    __tablename__ = "budget_allocations"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    category = Column(String, nullable=False)
    allocated = Column(Float, nullable=False)
    spent = Column(Float, default=0.0)
    icon_name = Column(String, nullable=True)
    
    budget = relationship("Budget", back_populates="allocations")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    trip_id = Column(Integer, ForeignKey("trips.id"))
    category = Column(String, nullable=False)
    category_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    is_planned = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    budget = relationship("Budget", back_populates="expenses")