from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import auth, models
from app.schemas.inventory import (
    Inventory, InventoryCreate, InventoryUpdate,
    InventoryTransaction, InventoryTransactionCreate,
    StockAlert
)

router = APIRouter(prefix="/inventory", tags=["inventory"])

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_current_user(token, db)

# ============== FIX: ADD THIS MISSING GET ENDPOINT ==============
# Get all inventory items for a business
@router.get("/", response_model=List[Inventory])
def get_inventory(
    business_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify business ownership
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    # Get all inventory items for the business
    items = db.query(models.Inventory).filter(
        models.Inventory.business_id == business_id
    ).offset(skip).limit(limit).all()
    
    return items
# =================================================================

# Get single inventory item
@router.get("/{item_id}", response_model=Inventory)
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.Inventory).join(
        models.Business, models.Business.id == models.Inventory.business_id
    ).filter(
        models.Inventory.id == item_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    return item

# Create inventory item
@router.post("/", response_model=Inventory)
def create_inventory_item(
    item: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == item.business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    db_item = models.Inventory(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Check for low stock and create alert
    if db_item.quantity <= db_item.reorder_level:
        create_low_stock_alert(db, db_item)
    
    return db_item

# Update inventory item
@router.put("/{item_id}", response_model=Inventory)
def update_inventory_item(
    item_id: int,
    item_update: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.Inventory).join(
        models.Business, models.Business.id == models.Inventory.business_id
    ).filter(
        models.Inventory.id == item_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item

# Delete inventory item
@router.delete("/{item_id}")
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.Inventory).join(
        models.Business, models.Business.id == models.Inventory.business_id
    ).filter(
        models.Inventory.id == item_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    db.delete(item)
    db.commit()
    return {"message": "Inventory item deleted successfully"}

# Add stock
@router.post("/{item_id}/add-stock", response_model=InventoryTransaction)
def add_stock(
    item_id: int,
    quantity: float,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.Inventory).join(
        models.Business, models.Business.id == models.Inventory.business_id
    ).filter(
        models.Inventory.id == item_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    item.quantity += quantity
    
    transaction = models.InventoryTransaction(
        inventory_id=item_id,
        quantity_change=quantity,
        transaction_type="purchase",
        notes=notes or f"Added {quantity} {item.unit}"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

# Remove stock
@router.post("/{item_id}/remove-stock", response_model=InventoryTransaction)
def remove_stock(
    item_id: int,
    quantity: float,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.Inventory).join(
        models.Business, models.Business.id == models.Inventory.business_id
    ).filter(
        models.Inventory.id == item_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    if item.quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {item.quantity} {item.unit}"
        )
    
    item.quantity -= quantity
    
    transaction = models.InventoryTransaction(
        inventory_id=item_id,
        quantity_change=-quantity,
        transaction_type="sale",
        notes=notes or f"Removed {quantity} {item.unit}"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

# Get low stock alerts
@router.get("/alerts/low-stock", response_model=List[StockAlert])
def get_low_stock_alerts(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    items = db.query(models.Inventory).filter(
        models.Inventory.business_id == business_id,
        models.Inventory.quantity <= models.Inventory.reorder_level
    ).all()
    
    alerts = []
    for item in items:
        alerts.append({
            "inventory_id": item.id,
            "name": item.name,
            "sku": item.sku,
            "current_quantity": item.quantity,
            "reorder_level": item.reorder_level,
            "deficit": item.reorder_level - item.quantity
        })
    
    return alerts

# Get inventory transactions
@router.get("/{item_id}/transactions", response_model=List[InventoryTransaction])
def get_inventory_transactions(
    item_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.Inventory).join(
        models.Business, models.Business.id == models.Inventory.business_id
    ).filter(
        models.Inventory.id == item_id,
        models.Business.owner_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    return db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.inventory_id == item_id
    ).order_by(models.InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()

def create_low_stock_alert(db: Session, item: models.Inventory):
    """Create a low stock alert"""
    # Check if Alert model exists, if not, just print for now
    try:
        alert = models.Alert(
            business_id=item.business_id,
            inventory_id=item.id,
            type="low_stock",
            message=f"Low stock: {item.name} has {item.quantity} {item.unit} (reorder at {item.reorder_level})",
            severity="warning",
            resolved=False
        )
        db.add(alert)
        db.commit()
    except Exception as e:
        print(f"Alert model not available yet: {e}")
