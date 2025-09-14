from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from deps import get_current_user
from database import get_db
from Models.budget import Budget, Expense, BudgetAllocation
import models 
from Schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetRead,
    ExpenseCreate, ExpenseUpdate, ExpenseRead
)

router = APIRouter(prefix="/user", tags=["Budget & Expenses"])


# GET /user/budgets
@router.get("/budgets", response_model=dict)
def get_user_budgets(user_id: int, db: Session = Depends(get_db)):
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    # For MVP, pick latest budget as "current"
    current = budgets[-1] if budgets else None
    return {"budgets": budgets, "current": current}


# POST /user/budgets
@router.post("/budgets", response_model=BudgetRead)
def create_budget(
    budget: BudgetCreate,
    user : models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)):
    # Check if a budget already exists for this trip
    existing_budget = db.query(Budget).filter(Budget.trip_id == budget.trip_id).first()
    if existing_budget:
        raise HTTPException(status_code=400, detail="Budget has already been created for this trip.")

    new_budget = Budget(
        user_id=user.id,
        trip_id=budget.trip_id,
        amount=budget.amount,
        yearly_budget_id = budget.yearly_budget_id
    )
    db.add(new_budget)
    db.flush()  # Get budget.id before allocations

    for alloc in budget.allocatedBreakdown:
        db.add(BudgetAllocation(
            budget_id=new_budget.id,
            category=alloc.category,
            allocated=alloc.allocated,
            icon_name=alloc.icon_name
        ))

    db.commit()
    db.refresh(new_budget)
    print(new_budget)
    return new_budget


# PATCH /user/budgets/:id
@router.patch("/budgets/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, updates: BudgetUpdate, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if updates.amount is not None:
        budget.amount = updates.amount

    if updates.allocatedBreakdown:
        db.query(BudgetAllocation).filter(BudgetAllocation.budget_id == budget.id).delete()
        for alloc in updates.allocatedBreakdown:
            db.add(BudgetAllocation(
                budget_id=budget.id,
                category=alloc.category,
                allocated=alloc.allocated,
                icon_name=alloc.icon_name
            ))

    db.commit()
    db.refresh(budget)
    return budget


# GET /user/expenses
@router.get("/expenses", response_model=dict)
def get_expenses(trip_id: int, db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    total = sum(e.amount for e in expenses)
    return {"expenses": expenses, "total": total, "page": 1}


# POST /user/expenses
@router.post("/expenses", response_model=ExpenseRead)
def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    new_exp = Expense(**expense.dict())
    db.add(new_exp)
    db.commit()
    db.refresh(new_exp)
    return new_exp


# PATCH /user/expenses/:id
@router.patch("/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense(expense_id: int, updates: ExpenseUpdate, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(expense, key, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", response_model=dict)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"success": True, "deleted_id": expense_id}


@router.get("/budgets/yearly/{yearly_trip_id}", response_model=dict)
def get_yearly_trip_budgets(
    yearly_trip_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all budgets for the current user that belong to a specific yearly_trip_id.
    """
    budgets = (
        db.query(Budget)
        .filter(Budget.user_id == user.id, Budget.yearly_budget_id == yearly_trip_id)
        .all()
    )
    if not budgets:
        raise HTTPException(status_code=404, detail="No budgets found for this yearly trip.")
    return {"budgets": budgets, "count": len(budgets)}
