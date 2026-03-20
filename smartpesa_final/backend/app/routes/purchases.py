from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.purchase_batch import PurchaseBatch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement, MovementReason
from app.schemas.purchase_batch import PurchaseBatchCreate, PurchaseBatch as PurchaseBatchSchema

router = APIRouter(tags=["Purchases"])

@router.post("/", response_model=PurchaseBatchSchema)
def create_purchase(purchase: PurchaseBatchCreate, db: Session = Depends(get_db)):
    db_purchase = PurchaseBatch(
        product_id=purchase.product_id,
        quantity=purchase.quantity,
        cost_per_unit=purchase.cost_per_unit,
        purchase_date=purchase.purchase_date,
        remaining_quantity=purchase.quantity,
        supplier_id=purchase.supplier_id,
        notes=purchase.notes
    )
    db.add(db_purchase)
    db.flush()

    inventory = db.query(Inventory).filter(Inventory.id == purchase.product_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Product not found")
    inventory.quantity = (inventory.quantity or 0) + purchase.quantity

    movement = InventoryMovement(
        product_id=purchase.product_id,
        quantity_change=purchase.quantity,
        reason=MovementReason.purchase,
        reference_id=db_purchase.id,
        notes="Purchase batch created"
    )
    db.add(movement)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

@router.get("/", response_model=List[PurchaseBatchSchema])
def list_purchases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    purchases = db.query(PurchaseBatch).offset(skip).limit(limit).all()
    return purchases
