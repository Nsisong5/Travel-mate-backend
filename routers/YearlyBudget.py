from fastapi import FastAPI, Depends, HTTPException, APIRouter 
from sqlalchemy.orm import Session
from typing import List
from deps import get_current_user
import models as Models
import Models.YearlyBudget as models
from database import engine, get_db
import Schemas.YearlyBudget as schemas 

router  = APIRouter(prefix="/yearly")

# CRUD Endpoints for YearlyBudget

@router.post("/budgets/", response_model=schemas.YearlyBudgetResponse)
def create_yearly_budget(
 budget: schemas.YearlyBudgetCreate,
 db: Session = Depends(get_db),
 user: Models.User = Depends(get_current_user)):
    """
    Creates a new yearly budget entry.
    """
    # Check if a budget for that year already exists
    db_budget = db.query(models.YearlyBudget).filter(models.YearlyBudget.user_id == user.id).first()
    if db_budget:
        raise HTTPException(status_code=400, detail="Budget for this year already exists")
        
        # Create the new database entry
    db_budget = models.YearlyBudget(
       total = budget.total,
       used = budget.used,
       year = budget.year,
       user_id = user.id
       
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.get("/budgets/", response_model=List[schemas.YearlyBudgetResponse])
def get_all_yearly_budgets(db: Session = Depends(get_db)):
    """
    Retrieves all yearly budget entries.
    """
    budgets = db.query(models.YearlyBudget).all()
    return budgets

@router.get("/budgets/{budget_id}", response_model=schemas.YearlyBudgetResponse)
def get_yearly_budget(budget_id: int, db: Session = Depends(get_db),
    user: Models.User = Depends(get_current_user)):
    """
    Retrieves a single yearly budget entry by its ID.
    """
    budget = db.query(models.YearlyBudget).filter(models.YearlyBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

@router.patch("/budgets/", response_model=schemas.YearlyBudgetResponse)
def update_yearly_budget(
    budget: schemas.YearlyBudgetUpdate, 
    db: Session = Depends(get_db),
    user: Models.User = Depends(get_current_user)):
    """
    Updates an existing yearly budget entry.
    """
    print(user.yearly_budget_id)
    db_budget = db.query(models.YearlyBudget).filter(models.YearlyBudget.id == user.yearly_budget_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Update only the fields that were provided in the request
    update_data = budget.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_budget, key, value)

    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.delete("/budgets/{budget_id}", status_code=204)
def delete_yearly_budget(budget_id: int, db: Session = Depends(get_db),
     user: Models.User = Depends(get_current_user)):
    """
    Deletes a yearly budget entry.
    """
    db_budget = db.query(models.YearlyBudget).filter(models.YearlyBudget.id == budget_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(db_budget)
    db.commit()
    return {"message": "Budget deleted successfully"}
    