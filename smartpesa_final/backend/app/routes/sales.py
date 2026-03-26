from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.purchase_batch import PurchaseBatch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement, MovementReason
from app.models.transaction import Transaction
from app.schemas.sale import SaleCreate, Sale as SaleSchema

router = APIRouter(tags=["Sales"])

def calculate_cogs_fifo(product_id: int, quantity_sold: int, db: Session):
    batches = db.query(PurchaseBatch).filter(
        PurchaseBatch.product_id == product_id,
        PurchaseBatch.remaining_quantity > 0
    ).order_by(PurchaseBatch.purchase_date).all()
    
    remaining = quantity_sold
    total_cost = 0
    for batch in batches:
        take = min(batch.remaining_quantity, remaining)
        total_cost += take * batch.cost_per_unit
        batch.remaining_quantity -= take
        remaining -= take
        if remaining == 0:
            break
    if remaining > 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    return total_cost

@router.post("/", response_model=SaleSchema)
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    db_sale = Sale(
        business_id=sale.business_id,
        payment_method=sale.payment_method,
        customer_name=sale.customer_name,
        notes=sale.notes,
        total_amount=0
    )
    db.add(db_sale)
    db.flush()

    total = 0
    for item in sale.items:
        cogs = calculate_cogs_fifo(item.product_id, item.quantity, db)
        db_item = SaleItem(
            sale_id=db_sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            cost_of_goods_sold=cogs,
            discount=item.discount
        )
        db.add(db_item)

        inventory = db.query(Inventory).filter(Inventory.id == item.product_id).first()
        if not inventory:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        inventory.quantity -= item.quantity

        movement = InventoryMovement(
            product_id=item.product_id,
            quantity_change=-item.quantity,
            reason=MovementReason.sale,
            reference_id=db_item.id,
            notes="Sale item"
        )
        db.add(movement)

        total += item.quantity * item.unit_price - item.discount

    db_sale.total_amount = total

    # Create a corresponding transaction record for this sale
    transaction = Transaction(
        business_id=sale.business_id,
        amount=total,
        type='income',
        category='Sales',
        description=f"Sale #{db_sale.id} - {sale.customer_name or 'Walk-in'}",
        reference=f"SALE-{db_sale.id}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)

    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.get("/", response_model=List[SaleSchema])
def list_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sales = db.query(Sale).offset(skip).limit(limit).all()
    return sales

@router.get("/{sale_id}", response_model=SaleSchema)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale