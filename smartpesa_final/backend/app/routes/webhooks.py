"""
Webhooks routes for SmartPesa API (placeholder)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint"""
    return {"status": "received"}

@router.post("/mpesa")
async def mpesa_webhook(request: Request):
    """M-Pesa webhook endpoint"""
    return {"status": "received"}
