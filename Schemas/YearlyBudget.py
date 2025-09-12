from pydantic import BaseModel
from typing import Optional

class YearlyBudgetBase(BaseModel):
    """Base schema for yearly budget data."""
    total: float
    used: float
    year: int


class YearlyBudgetCreate(YearlyBudgetBase):
    """Schema for creating a new yearly budget."""
    pass

class YearlyBudgetUpdate(BaseModel):
    """Schema for updating an existing yearly budget."""
    total: Optional[float] = None
    used: Optional[float] = None
    year: Optional[int] = None

class YearlyBudgetResponse(YearlyBudgetBase):
    """Schema for the API response, including the ID."""
    id: int

    class Config:
        """Pydantic configuration."""
        # This tells Pydantic to read the data even if it's not a dict, but an ORM object (like a SQLAlchemy model)
        from_attributes = True 
        