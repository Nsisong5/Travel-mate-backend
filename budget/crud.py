from sqlalchemy.orm import Session
import models, schemas

def create_budget(db: Session, user_id: int, budget: schemas.BudgetCreate):
    db_budget = models.Budget(
        user_id=user_id,
        amount=budget.amount,
        period=budget.period,
        purpose=budget.purpose
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

def get_user_budgets(db: Session, user_id: int):
    return db.query(models.Budget).filter(models.Budget.user_id == user_id).all()