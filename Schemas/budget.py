
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BudgetAllocationBase(BaseModel):
    category: str
    allocated: float
    spent: Optional[float] = 0.0
    icon_name: Optional[str]

class BudgetAllocationCreate(BudgetAllocationBase):
    pass

class BudgetAllocationRead(BudgetAllocationBase):
    id: int
    class Config:
        orm_mode = True


class ExpenseBase(BaseModel):
    category: str
    category_name: str
    description: Optional[str]
    amount: float
    is_planned: bool
    date: datetime
    trip_id: int

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    category: Optional[str]
    category_name: Optional[str]
    description: Optional[str]
    amount: Optional[float]
    is_planned: Optional[bool]
    date: Optional[datetime]

class ExpenseRead(ExpenseBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True


class BudgetBase(BaseModel):
    trip_id: int
    amount: float
    period: str = "trip"

class BudgetCreate(BudgetBase):
    allocatedBreakdown: List[BudgetAllocationCreate]

class BudgetUpdate(BaseModel):
    amount: Optional[float]
    allocatedBreakdown: Optional[List[BudgetAllocationCreate]]

class BudgetRead(BudgetBase):
    id: int
    user_id: int
    trip_name: Optional[str]
    allocatedBreakdown: List[BudgetAllocationRead]
    confirmedSpent: float
    plannedSpent: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True