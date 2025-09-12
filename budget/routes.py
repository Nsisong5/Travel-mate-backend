# routes/budget.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, database, auth.auth as auth
from budget import crud

router = APIRouter(prefix="/budget", tags=["budget"])

@router.post("/", response_model=schemas.BudgetResponse)
def create_budget(budget: schemas.BudgetCreate, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    return crud.create_budget(db=db, user_id=current_user["id"], budget=budget)

@router.get("/", response_model=list[schemas.BudgetResponse])
def get_budgets(db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    return crud.get_user_budgets(db, user_id=current_user["id"])