from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os
import shutil
from app.database import get_db
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.transaction import Transaction
from app.models.business import Business          # <-- added import
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.schemas.expense_category import ExpenseCategoryResponse, ExpenseCategoryCreate
from app.routes.users import get_current_user
from app.models.user import User

router = APIRouter(tags=["Expenses"])

UPLOAD_DIR = "uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- Expense Categories ----------
@router.get("/categories", response_model=List[ExpenseCategoryResponse])
def get_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ExpenseCategory).all()

@router.post("/categories", response_model=ExpenseCategoryResponse)
def create_category(category: ExpenseCategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_cat = ExpenseCategory(**category.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

# ---------- Expenses ----------
@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Expense)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify category exists
    category = db.get(ExpenseCategory, expense.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Verify business exists and belongs to current user
    business = db.query(Business).filter(
        Business.id == expense.business_id,
        Business.owner_id == current_user.id
    ).first()
    if not business:
        raise HTTPException(status_code=403, detail="Business not found or access denied")

    # Create expense record
    db_expense = Expense(**expense.dict(exclude={'business_id'}))
    db.add(db_expense)
    db.flush()

    # Create transaction record
    transaction = Transaction(
        business_id=expense.business_id,
        amount=expense.amount,
        type='expense',
        category=category.name,
        description=expense.description or f"Expense: {category.name}",
        reference=f"EXP-{db_expense.id}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)

    db.commit()
    db.refresh(db_expense)
    return db_expense

@router.post("/{expense_id}/receipt")
async def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404)

    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{expense_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    expense.receipt_image = file_path
    db.commit()
    return {"filename": file_path}

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404)
    return expense

@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404)
    for key, value in expense_update.dict(exclude_unset=True).items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404)
    db.delete(expense)
    db.commit()
    return