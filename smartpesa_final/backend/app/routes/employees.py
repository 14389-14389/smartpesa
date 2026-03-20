from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.employee import Employee
from app.models.employee_rank import EmployeeRank
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.employee_rank import EmployeeRankCreate, EmployeeRankUpdate, EmployeeRankResponse
from app.routes.users import get_current_user
from app.models.user import User

router = APIRouter(tags=["Employees"])

# ---------- Employee Ranks ----------
@router.get("/ranks", response_model=List[EmployeeRankResponse])
def get_ranks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(EmployeeRank).all()

@router.post("/ranks", response_model=EmployeeRankResponse, status_code=status.HTTP_201_CREATED)
def create_rank(rank: EmployeeRankCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_rank = EmployeeRank(**rank.dict())
    db.add(db_rank)
    db.commit()
    db.refresh(db_rank)
    return db_rank

@router.put("/ranks/{rank_id}", response_model=EmployeeRankResponse)
def update_rank(
    rank_id: int,
    rank_update: EmployeeRankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rank = db.get(EmployeeRank, rank_id)
    if not rank:
        raise HTTPException(status_code=404, detail="Rank not found")
    for key, value in rank_update.dict(exclude_unset=True).items():
        setattr(rank, key, value)
    db.commit()
    db.refresh(rank)
    return rank

@router.delete("/ranks/{rank_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rank(
    rank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rank = db.get(EmployeeRank, rank_id)
    if not rank:
        raise HTTPException(status_code=404, detail="Rank not found")

    # Check if any employees still use this rank
    employees_with_rank = db.query(Employee).filter(Employee.rank_id == rank_id).first()
    if employees_with_rank:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete rank because there are employees assigned to it. Remove or reassign employees first."
        )
    db.delete(rank)
    db.commit()
    return

# ---------- Employees ----------
@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Employee)
    if active_only:
        query = query.filter(Employee.is_active == True)
    return query.all()

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify rank exists
    rank = db.get(EmployeeRank, employee.rank_id)
    if not rank:
        raise HTTPException(status_code=404, detail="Rank not found")
    db_employee = Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404)
    return employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404)
    for key, value in employee_update.dict(exclude_unset=True).items():
        setattr(employee, key, value)
    db.commit()
    db.refresh(employee)
    return employee

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404)
    db.delete(employee)
    db.commit()
    return