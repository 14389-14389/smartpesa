from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.employee import Employee
from app.models.salary_payment import SalaryPayment
from app.models.transaction import Transaction
from app.schemas.salary_payment import SalaryPaymentCreate, SalaryPaymentResponse
from app.routes.users import get_current_user
from app.models.user import User

router = APIRouter(tags=["Salary Payments"])

@router.get("/", response_model=List[SalaryPaymentResponse])
def get_salary_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SalaryPayment).offset(skip).limit(limit).all()

@router.post("/", response_model=SalaryPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_salary_payment(
    payment: SalaryPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify employee exists and is active
    employee = db.get(Employee, payment.employee_id)
    if not employee or not employee.is_active:
        raise HTTPException(status_code=404, detail="Employee not found or inactive")

    # Ensure business_id is provided
    if not payment.business_id:
        raise HTTPException(status_code=400, detail="Business ID is required")

    # Create the salary payment record
    db_payment = SalaryPayment(**payment.dict())
    db.add(db_payment)
    db.flush()

    # Create a transaction record for this expense
    transaction = Transaction(
        business_id=payment.business_id,
        amount=payment.amount,
        type='expense',
        category='Salary',
        description=f"Salary payment for {employee.name} - {payment.month}",
        reference=f"SAL-{db_payment.id}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)

    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.get("/{payment_id}", response_model=SalaryPaymentResponse)
def get_salary_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.get(SalaryPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_salary_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.get(SalaryPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(payment)
    db.commit()
    return