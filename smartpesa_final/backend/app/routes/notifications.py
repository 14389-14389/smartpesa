"""
Notifications routes for SmartPesa API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Notification
from app.utils.auth import get_current_user
from app.utils.validators import validate_business_access

router = APIRouter()

class NotificationCreate(BaseModel):
    business_id: int
    title: str
    message: str
    type: str = "info"
    priority: str = "normal"
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None

@router.get("/")
async def get_notifications(
    business_id: int = Query(...),
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for a business"""
    # Verify business access
    business = await validate_business_access(business_id, current_user.id, db)
    
    query = db.query(Notification).filter(Notification.business_id == business_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [n.to_dict() for n in notifications],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{notification_id}")
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await validate_business_access(notification.business_id, current_user.id, db)
    
    return {
        "success": True,
        "data": notification.to_dict()
    }

@router.post("/", status_code=201)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification"""
    await validate_business_access(notification.business_id, current_user.id, db)
    
    db_notification = Notification(
        business_id=notification.business_id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        priority=notification.priority,
        action_url=notification.action_url,
        expires_at=notification.expires_at
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return {
        "success": True,
        "data": db_notification.to_dict(),
        "message": "Notification created successfully"
    }

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await validate_business_access(notification.business_id, current_user.id, db)
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    
    return {
        "success": True,
        "data": notification.to_dict(),
        "message": "Notification marked as read"
    }

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for a business"""
    await validate_business_access(business_id, current_user.id, db)
    
    result = db.query(Notification).filter(
        Notification.business_id == business_id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.utcnow()
    })
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Marked {result} notifications as read",
        "count": result
    }

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await validate_business_access(notification.business_id, current_user.id, db)
    
    db.delete(notification)
    db.commit()
    
    return {
        "success": True,
        "message": "Notification deleted successfully"
    }
